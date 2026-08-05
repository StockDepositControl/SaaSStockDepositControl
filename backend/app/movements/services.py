import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Tuple, List, Optional
from backend.app.movements.models import (
    TipoAccion,
    AuditEntryInput,
    AuditEntryResult,
    AuditBatchInput,
    AuditBatchResult,
    AuditoriaRegistroCreate,
)
from backend.app.movements.ports import StockRepositoryPort, AuditRepositoryPort
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException

class AuditService:
    """
    Pure domain service orchestrating audit registration, discrepancy calculations,
    and financial valorization rules.
    """
    def __init__(
        self,
        stock_repository: StockRepositoryPort,
        audit_repository: AuditRepositoryPort,
        default_vat_rate: Decimal = Decimal("0.21"),
    ):
        self.stock_repository = stock_repository
        self.audit_repository = audit_repository
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
        self, tenant_id: str, id_usuario: int, entry: AuditEntryInput
    ) -> AuditEntryResult:
        """
        Registers a single physical count entry, computes discrepancy and financial impact,
        updates physical stock, and persists movement audit log.
        Auto-generates backend timestamp and client_uuid.
        """
        client_uuid = str(uuid.uuid4())
        scan_timestamp = datetime.now(timezone.utc)

        # Fallback for sucursal and deposito if missing
        try:
            numeric_tenant = int(tenant_id)
        except (ValueError, TypeError):
            numeric_tenant = 1

        id_sucursal = entry.id_sucursal if entry.id_sucursal is not None else numeric_tenant
        id_deposito = entry.id_deposito if entry.id_deposito is not None else numeric_tenant

        # 1. Retrieve stock position
        stock_pos = await self.stock_repository.get_stock_position(
            tenant_id=tenant_id,
            id_sucursal=id_sucursal,
            id_deposito=id_deposito,
            id_articulo=entry.id_articulo,
        )
        if not stock_pos:
            raise EntityNotFoundException(
                f"Stock position not found for article '{entry.id_articulo}' in deposit '{id_deposito}'."
            )

        # 2. Retrieve cost and VAT classification
        pcio_com_siva, des_familia = await self.stock_repository.get_article_cost_info(
            tenant_id=tenant_id, id_articulo=entry.id_articulo
        )

        # 3. Compute discrepancy and financial value using stock_real
        delta_stock, tipo_accion = self.compute_delta(
            stock_real_previo=stock_pos.stock_real,
            stock_fisico_contado=entry.stock_fisico_contado,
        )

        cantidad_afectada = abs(delta_stock)
        monto_valorizado = self.compute_valorized_amount(
            pcio_com_siva=pcio_com_siva,
            des_familia=des_familia,
            cantidad=cantidad_afectada,
            default_vat_rate=self.default_vat_rate,
        )

        # 4. Modify physical stock directly in repository
        await self.stock_repository.update_stock_real(
            tenant_id=tenant_id,
            id_sucursal=id_sucursal,
            id_deposito=id_deposito,
            id_articulo=entry.id_articulo,
            new_stock_real=entry.stock_fisico_contado,
        )

        # 5. Persist audit record
        record_to_create = AuditoriaRegistroCreate(
            tenant_id=tenant_id,
            id_sucursal=id_sucursal,
            id_deposito=id_deposito,
            id_articulo=entry.id_articulo,
            tipo_accion=tipo_accion,
            cantidad_afectada=cantidad_afectada,
            monto_valorizado=monto_valorizado,
            id_usuario=id_usuario,
            fecha_hora=scan_timestamp,
            client_uuid=client_uuid,
            observacion=entry.observacion,
            tipo_accion_auditoria=entry.tipo_accion_auditoria,
        )

        saved_record = await self.audit_repository.create_audit_record(record_to_create)

        return AuditEntryResult(
            client_uuid=client_uuid,
            id_articulo=entry.id_articulo,
            stock_real=stock_pos.stock_real,
            stock_fisico_contado=entry.stock_fisico_contado,
            delta_stock=delta_stock,
            tipo_accion=tipo_accion,
            cantidad_afectada=cantidad_afectada,
            monto_valorizado=monto_valorizado,
            id_auditoria=saved_record.id_auditoria if saved_record else None,
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
