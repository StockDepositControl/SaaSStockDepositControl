import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple, List, Optional
from backend.app.movements.domain import (
    TipoAccion,
    AuditRecordCreate,
    StockLookupResult,
)
from backend.app.movements.schemas import (
    AuditEntryRequest,
    AuditEntryResult,
    AuditBatchInput,
    AuditBatchResult,
)
from backend.app.movements.ports import StockRepositoryPort, AuditRepositoryPort
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException
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


class AuditService:
    """
    Pure domain service orchestrating audit registration, discrepancy calculations,
    and financial valorization rules.
    """
    def __init__(
        self,
        stock_repository: StockRepositoryPort,
        audit_repository: AuditRepositoryPort,
        stock_lookup_service: StockLookupService,
        work_session_service: WorkSessionService,
        default_vat_rate: Decimal = Decimal("0.21"),
    ):
        self.stock_repository = stock_repository
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
        """
        delta = stock_fisico_contado - stock_real_previo
        if delta > 0:
            return delta, TipoAccion.ALTA
        elif delta < 0:
            return delta, TipoAccion.BAJA
        else:
            return 0, TipoAccion.SIN_ACCION

    @staticmethod
    def compute_valorized_amount(
        pcio_com_siva: Decimal,
        des_familia: Optional[str],
        cantidad: int,
        default_vat_rate: Decimal = Decimal("0.21"),
    ) -> Decimal:
        """
        Calculates valorized amount based on purchase cost and family VAT classification.
        'Medicamentos' family incurs 0% VAT. All other families incur default_vat_rate (e.g. 21%).
        """
        family_clean = (des_familia or "").strip().lower()
        if family_clean == "medicamentos":
            vat_rate = Decimal("0.00")
        else:
            vat_rate = default_vat_rate

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

        # Fallback for sucursal and deposito if missing
        id_sucursal = entry.id_sucursal if entry.id_sucursal is not None else 1
        id_deposito = entry.id_deposito if entry.id_deposito is not None else 1

        try:
            tenant_id_int = int(tenant_id)
        except (ValueError, TypeError):
            tenant_id_int = 1

        # 1. Retrieve stock position using lookup service
        stock_lookup = await self.stock_lookup_service.get_effective_stock(
            tenant_id=tenant_id_int,
            id_sucursal=id_sucursal,
            id_deposito=id_deposito,
            id_articulo=entry.id_articulo,
        )

        # 2. Retrieve cost and VAT classification
        pcio_com_siva, des_familia = await self.stock_repository.get_article_cost_info(
            id_articulo=entry.id_articulo
        )
 
        # 3. Compute discrepancy, final audit_quantity, and action type
        if entry.stock_fisico_contado is not None:
            delta_stock, tipo_accion = self.compute_delta(
                stock_real_previo=stock_lookup.stock_real,
                stock_fisico_contado=entry.stock_fisico_contado,
            )
            cantidad_afectada = abs(delta_stock)
            audit_quantity = entry.stock_fisico_contado
            stock_fisico_contado_val = entry.stock_fisico_contado
        elif entry.cantidad_afectada is not None and entry.tipo_accion is not None:
            cantidad_afectada = abs(entry.cantidad_afectada)
            tipo_accion = entry.tipo_accion
            if tipo_accion == TipoAccion.BAJA:
                delta_stock = -cantidad_afectada
                audit_quantity = stock_lookup.stock_real - cantidad_afectada
            elif tipo_accion == TipoAccion.ALTA:
                delta_stock = cantidad_afectada
                audit_quantity = stock_lookup.stock_real + cantidad_afectada
            else:
                delta_stock = 0
                audit_quantity = stock_lookup.stock_real
            stock_fisico_contado_val = audit_quantity
        else: #This will be dead code after refactoring, but kept for backward compatibility
            raise BusinessRuleViolationException(
                "Either stock_fisico_contado or (cantidad_afectada and tipo_accion) must be provided."
            )

        family_clean = (des_familia or "").strip().lower()
        applied_vat_rate = Decimal("0.00") if family_clean == "medicamentos" else self.default_vat_rate

        monto_valorizado = self.compute_valorized_amount(
            pcio_com_siva=pcio_com_siva,
            des_familia=des_familia,
            cantidad=cantidad_afectada,
            default_vat_rate=self.default_vat_rate,
        )

        # 5. Retrieve active work session ID or default fallback
        active_session_id = await self.work_session_service.get_active_session_id(id_sucursal)
        session_id = active_session_id if active_session_id is not None else 1

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
