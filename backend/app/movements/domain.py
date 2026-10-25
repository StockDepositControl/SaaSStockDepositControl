from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TipoAccion(str, Enum):
    ALTA = "Alta"
    BAJA = "Baja"
    SIN_ACCION = "Sin Acción"


class StockPorDepositoBase(BaseModel):
    id_empresa: int
    id_sucursal: int
    id_deposito: int
    id_articulo: str
    stock_real: int


class StockPorDepositoCreate(StockPorDepositoBase):
    pass


class StockPorDepositoUpdate(BaseModel):
    stock_real: Optional[int] = None


class StockPorDeposito(StockPorDepositoBase):
    model_config = ConfigDict(from_attributes=True)


class LotePorDepositoBase(BaseModel):
    id_empresa: int
    id_sucursal: int
    id_deposito: int
    id_articulo: str
    lote: str
    vencimiento: Optional[str] = None
    stock_real: int


class LotePorDepositoCreate(LotePorDepositoBase):
    pass


class LotePorDepositoUpdate(BaseModel):
    vencimiento: Optional[str] = None
    stock_real: Optional[int] = None


class LotePorDeposito(LotePorDepositoBase):
    model_config = ConfigDict(from_attributes=True)


class AuditRecordBase(BaseModel):
    session_id: int
    tenant_id: str
    branch_id: int
    warehouse_id: int
    article_code: str
    action_type: TipoAccion
    affected_amount: int
    audit_quantity: int
    applied_unit_cost: Decimal
    applied_vat_rate: Decimal
    valorized_amount: Decimal
    user_id: int
    scan_timestamp: datetime
    client_uuid: Optional[str] = None
    observation: Optional[str] = None


class AuditRecordCreate(AuditRecordBase):
    pass


class AuditRecord(AuditRecordBase):
    audit_id: int

    model_config = ConfigDict(from_attributes=True)


class StockLookupResult(BaseModel):
    id_articulo: str
    stock_real: int
    source: str


class SessionAuditAggregates(BaseModel):
    """
    Aggregated audit counters for a single work session, computed by the repository.
    Counts are distinct articles per action type.
    """

    audited_count: int = 0
    alta_count: int = 0
    baja_count: int = 0
    sin_accion_count: int = 0
    monto_valorizado_baja: Decimal = Decimal("0")
    monto_valorizado_alta: Decimal = Decimal("0")


class VatClassifier:
    """
    Pure Fabrication domain service encapsulating product family tax/VAT rate
    classification.
    'Medicamentos' family is tax-exempt (0% VAT). All other families incur
    default_vat_rate (e.g. 21%).
    """

    @staticmethod
    def classify(
        des_familia: Optional[str], default_vat_rate: Decimal = Decimal("0.21")
    ) -> Decimal:
        family_clean = (des_familia or "").strip().lower()
        if family_clean == "medicamentos":
            return Decimal("0.00")
        return default_vat_rate


class DeltaResult(BaseModel):
    """
    Result of a stock discrepancy delta calculation.
    """

    delta_stock: int
    tipo_accion: TipoAccion
    cantidad_afectada: int
    audit_quantity: int


class DeltaCalculator:
    """
    Pure Fabrication domain service for calculating physical count discrepancy deltas
    and applying stock variance impacts.
    """

    @staticmethod
    def from_physical_count(
        stock_real_previo: int, stock_fisico_contado: int
    ) -> DeltaResult:
        """
        Computes delta based on physical count observation:
        delta = stock_fisico_contado - stock_real_previo
        """
        delta = stock_fisico_contado - stock_real_previo
        if delta > 0:
            tipo_accion = TipoAccion.ALTA
        elif delta < 0:
            tipo_accion = TipoAccion.BAJA
        else:
            tipo_accion = TipoAccion.SIN_ACCION

        return DeltaResult(
            delta_stock=delta,
            tipo_accion=tipo_accion,
            cantidad_afectada=abs(delta),
            audit_quantity=stock_fisico_contado,
        )

    @staticmethod
    def from_variance(
        stock_real_previo: int, cantidad_afectada: int, tipo_accion: TipoAccion
    ) -> DeltaResult:
        """
        Computes delta and resulting audit quantity based on variance input.
        """
        abs_qty = abs(cantidad_afectada)
        if tipo_accion == TipoAccion.BAJA:
            delta_stock = -abs_qty
            audit_quantity = stock_real_previo - abs_qty
        elif tipo_accion == TipoAccion.ALTA:
            delta_stock = abs_qty
            audit_quantity = stock_real_previo + abs_qty
        else:
            delta_stock = 0
            audit_quantity = stock_real_previo

        return DeltaResult(
            delta_stock=delta_stock,
            tipo_accion=tipo_accion,
            cantidad_afectada=abs_qty,
            audit_quantity=audit_quantity,
        )
