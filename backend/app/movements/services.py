import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple, List, Optional, Dict
from backend.app.movements.domain import (
    TipoAccion,
    AuditRecordCreate,
    StockLookupResult,
    VatClassifier,
    DeltaCalculator,
    DeltaResult,
)
from backend.app.movements.schemas import (
    AuditEntryRequest,
    AuditEntryResult,
    AuditBatchInput,
    AuditBatchResult,
    DashboardKPIsPublicOut,
    DashboardKPIsResponse,
)
from backend.app.movements.ports import StockRepositoryPort, AuditRepositoryPort
from backend.app.articles.ports import ArticleRepositoryPort
from backend.app.exceptions import (
    EntityNotFoundException,
    BusinessRuleViolationException,
    NoActiveWorkSessionError,
)
from backend.app.work_sessions.services import WorkSessionService

class StockLookupService:
    def __init__(self, stock_repository: StockRepositoryPort, audit_repository: AuditRepositoryPort):
        self.stock_repository = stock_repository
        self.audit_repository = audit_repository

    async def get_effective_stock(
        self, tenant_id: int, id_sucursal: int, id_deposito: int, id_articulo: str
    ) -> StockLookupResult:
        latest_audit = await self.audit_repository.get_latest_audit_record(
            tenant_id, id_sucursal, id_deposito, id_articulo
        )
        if latest_audit:
            return StockLookupResult(
                id_articulo=id_articulo,
                stock_real=latest_audit.audit_quantity,
                source="db_analytics"
            )

        stock_pos = await self.stock_repository.get_stock_position(
            tenant_id, id_sucursal, id_deposito, id_articulo
        )
        if not stock_pos:
            raise EntityNotFoundException(
                f"Stock position not found for article '{id_articulo}' in deposit '{id_deposito}'."
            )
        
        return StockLookupResult(
            id_articulo=id_articulo,
            stock_real=stock_pos.stock_real,
            source="db_articles"
        )

    async def get_effective_stocks_batch(
        self, article_ids: List[str], deposit_id: int, active_session_id: Optional[int] = None
    ) -> Dict[str, int]:
        """
        Resolves effective stock positions in batch for a list of articles in a deposit.
        1. Checks for latest active audit records in db_analytics.
        2. Queries stock positions in db_articles for remaining articles.
        3. Returns combined mapping {id_articulo: stock_real}.
        """
        if not article_ids:
            return {}

        audit_map: Dict[str, int] = {}
        if active_session_id:
            audit_map = await self.audit_repository.get_latest_audits_for_articles(
                session_id=active_session_id,
                article_ids=article_ids
            )

        remaining_ids = [aid for aid in article_ids if aid not in audit_map]

        stock_map: Dict[str, int] = {}
        if remaining_ids:
            stock_map = await self.stock_repository.get_stock_positions_batch(
                deposit_id=deposit_id,
                article_ids=remaining_ids
            )

        return {**stock_map, **audit_map}


class AuditService:
    """
    Pure domain service orchestrating audit registration, discrepancy calculations,
    and financial valorization rules.
    """
    def __init__(
        self,
        article_repository: ArticleRepositoryPort,
        audit_repository: AuditRepositoryPort,
        stock_lookup_service: StockLookupService,
        work_session_service: WorkSessionService,
        default_vat_rate: Decimal = Decimal("0.21"),
    ):
        self.article_repository = article_repository
        self.audit_repository = audit_repository
        self.stock_lookup_service = stock_lookup_service
        self.work_session_service = work_session_service
        self.default_vat_rate = default_vat_rate

    @staticmethod
    def compute_delta(stock_real_previo: int, stock_fisico_contado: int) -> Tuple[int, TipoAccion]:
        """
        Computes stock discrepancy delta:
        delta = stock_fisico_contado - stock_real_previo
        Returns (delta, TipoAccion).
        Delegates calculation to DeltaCalculator.
        """
        result = DeltaCalculator.from_physical_count(
            stock_real_previo=stock_real_previo,
            stock_fisico_contado=stock_fisico_contado,
        )
        return result.delta_stock, result.tipo_accion

    @staticmethod
    def compute_valorized_amount(
        pcio_com_siva: Decimal,
        des_familia: Optional[str],
        cantidad: int,
        default_vat_rate: Decimal = Decimal("0.21"),
    ) -> Decimal:
        """
        Calculates valorized amount based on purchase cost and family VAT classification.
        Delegates tax classification to VatClassifier.
        """
        vat_rate = VatClassifier.classify(des_familia, default_vat_rate)
        unit_cost_with_vat = pcio_com_siva * (Decimal("1.00") + vat_rate)
        return (unit_cost_with_vat * Decimal(abs(cantidad))).quantize(Decimal("0.0001"))

    async def register_single_audit(
        self, tenant_id: str, id_usuario: int, entry: AuditEntryRequest
    ) -> AuditEntryResult:
        """
        Registers a single physical count entry, computes discrepancy and financial impact,
        updates physical stock, and persists movement audit log.
        Auto-generates backend timestamp and client_uuid.
        """
        client_uuid = str(uuid.uuid4())
        scan_timestamp = datetime.now(timezone.utc)

        try:
            tenant_id_int = int(tenant_id)
        except (ValueError, TypeError):
            raise BusinessRuleViolationException(f"Invalid tenant_id '{tenant_id}'.")

        id_sucursal = entry.id_sucursal
        id_deposito = entry.id_deposito

        if id_sucursal is None or id_deposito is None:
            raise BusinessRuleViolationException(
                "Branch ID (id_sucursal) and Deposit ID (id_deposito) are required."
            )

        # 1. Retrieve stock position using lookup service
        stock_lookup = await self.stock_lookup_service.get_effective_stock(
            tenant_id=tenant_id_int,
            id_sucursal=id_sucursal,
            id_deposito=id_deposito,
            id_articulo=entry.id_articulo,
        )

        # 2. Retrieve article catalog data (cost and family) via ArticleRepositoryPort
        article = await self.article_repository.get_by_id(entry.id_articulo)
        if article is None:
            raise EntityNotFoundException(f"Article '{entry.id_articulo}' not found.")
        pcio_com_siva = article.pcio_com_siva
        des_familia = article.des_familia
 
        # 3. Compute discrepancy, final audit_quantity, and action type via DeltaCalculator
        if entry.stock_fisico_contado is not None:
            delta_result = DeltaCalculator.from_physical_count(
                stock_real_previo=stock_lookup.stock_real,
                stock_fisico_contado=entry.stock_fisico_contado,
            )
            stock_fisico_contado_val = entry.stock_fisico_contado
        elif entry.cantidad_afectada is not None and entry.tipo_accion is not None:
            delta_result = DeltaCalculator.from_variance(
                stock_real_previo=stock_lookup.stock_real,
                cantidad_afectada=entry.cantidad_afectada,
                tipo_accion=entry.tipo_accion,
            )
            stock_fisico_contado_val = delta_result.audit_quantity
        else:
            raise BusinessRuleViolationException(
                "Either stock_fisico_contado or (cantidad_afectada and tipo_accion) must be provided."
            )

        delta_stock = delta_result.delta_stock
        tipo_accion = delta_result.tipo_accion
        cantidad_afectada = delta_result.cantidad_afectada
        audit_quantity = delta_result.audit_quantity

        # 4. Tax/VAT classification and valorization
        applied_vat_rate = VatClassifier.classify(des_familia, self.default_vat_rate)

        monto_valorizado = self.compute_valorized_amount(
            pcio_com_siva=pcio_com_siva,
            des_familia=des_familia,
            cantidad=cantidad_afectada,
            default_vat_rate=self.default_vat_rate,
        )

        # 5. Retrieve active work session ID or raise domain exception
        active_session_id = await self.work_session_service.get_active_session_id(id_sucursal)
        if active_session_id is None:
            raise NoActiveWorkSessionError(
                f"No active work session found for branch '{id_sucursal}'."
            )
        session_id = active_session_id

        # 6. Persist audit record in db_analytics (db_articles remains untouched)
        record_to_create = AuditRecordCreate(
            session_id=session_id,
            tenant_id=tenant_id,
            branch_id=id_sucursal,
            warehouse_id=id_deposito,
            article_code=entry.id_articulo,
            action_type=tipo_accion,
            affected_amount=cantidad_afectada,
            audit_quantity=audit_quantity,
            applied_unit_cost=pcio_com_siva,
            applied_vat_rate=applied_vat_rate,
            valorized_amount=monto_valorizado,
            user_id=id_usuario,
            scan_timestamp=scan_timestamp,
            client_uuid=client_uuid,
            observation=entry.observation,
        )

        saved_record = await self.audit_repository.create_audit_record(record_to_create)

        return AuditEntryResult(
            client_uuid=client_uuid,
            id_articulo=entry.id_articulo,
            stock_real=stock_lookup.stock_real,
            stock_fisico_contado=stock_fisico_contado_val,
            delta_stock=delta_stock,
            tipo_accion=tipo_accion,
            cantidad_afectada=cantidad_afectada,
            audit_quantity=audit_quantity,
            monto_valorizado=monto_valorizado,
            audit_id=saved_record.audit_id if saved_record else None,
        )

    async def register_batch_audit(
        self, tenant_id: str, id_usuario: int, batch: AuditBatchInput
    ) -> AuditBatchResult:
        """
        Processes a batch of audit entries transmitted from offline mobile sync queue.
        """
        results: List[AuditEntryResult] = []
        duplicates_skipped = 0

        for entry in batch.items:
            try:
                res = await self.register_single_audit(tenant_id, id_usuario, entry)
                results.append(res)
            except BusinessRuleViolationException:
                duplicates_skipped += 1

        return AuditBatchResult(
            results=results,
            total_processed=len(results),
            duplicates_skipped=duplicates_skipped,
        )


class KPICalculator:
    """
    Pure Fabrication: stateless dashboard progress math, testable without any Port.
    """
    @staticmethod
    def pendientes(total_articulos: int, auditados: int) -> int:
        return max(0, total_articulos - auditados)

    @staticmethod
    def porcentaje_avance(total_articulos: int, auditados: int) -> int:
        if total_articulos <= 0:
            return 0
        return round((auditados / total_articulos) * 100)


class StockKPIService:
    """
    Read-only use case (CQS): orchestrates stock and audit ports to build dashboard KPIs.
    Financial amounts are returned only to administrators.
    """
    def __init__(self, stock_repository: StockRepositoryPort, audit_repository: AuditRepositoryPort):
        self.stock_repository = stock_repository
        self.audit_repository = audit_repository

    async def get_dashboard_kpis(
        self,
        tenant_id: str,
        branch_id: int,
        deposit_id: int,
        session_id: int,
        is_admin: bool,
    ) -> DashboardKPIsPublicOut:
        try:
            tenant_int = int(tenant_id)
        except (ValueError, TypeError):
            tenant_int = 1

        total = await self.stock_repository.count_catalog_articles()
        out_of_stock = await self.stock_repository.count_out_of_stock_articles(
            tenant_int, branch_id, deposit_id
        )
        agg = await self.audit_repository.get_session_audit_aggregates(
            tenant_int, branch_id, deposit_id, session_id
        )

        base = {
            "total_articulos": total,
            "auditados": agg.audited_count,
            "pendientes": KPICalculator.pendientes(total, agg.audited_count),
            "porcentaje_avance": KPICalculator.porcentaje_avance(total, agg.audited_count),
            "discrepancias_alta": agg.alta_count,
            "discrepancias_baja": agg.baja_count,
            "sin_accion": agg.sin_accion_count,
            "out_of_stock_count": out_of_stock,
        }

        if is_admin:
            return DashboardKPIsResponse(
                **base,
                monto_valorizado_baja=agg.monto_valorizado_baja,
                monto_valorizado_alta=agg.monto_valorizado_alta,
            )
        return DashboardKPIsPublicOut(**base)
