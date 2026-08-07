from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator

from backend.app.movements.domain import TipoAccion

class AuditEntryRequest(BaseModel):
    id_sucursal: Optional[int] = Field(default=None, ge=1, description="Branch/Store ID")
    id_deposito: Optional[int] = Field(default=None, ge=1, description="Warehouse/Deposit ID")
    id_articulo: str = Field(..., min_length=1, description="Article identifier (barcode or code)")
    stock_fisico_contado: Optional[int] = Field(default=None, ge=0, description="Physical count observed")
    cantidad_afectada: Optional[int] = Field(default=None, ge=0, description="Variance amount (absolute)")
    tipo_accion: Optional[TipoAccion] = Field(default=None, description="Action type for variance mode")
    observation: Optional[str] = Field(default=None, max_length=500, description="Operator note")

    @model_validator(mode="after")
    def validate_input_mode(self) -> "AuditEntryRequest":
        """
        Enforce input mode: the client must provide EITHER
        stock_fisico_contado (physical count mode) OR both cantidad_afectada
        and tipo_accion (variance mode). Providing neither is invalid.
        """
        has_count = self.stock_fisico_contado is not None
        has_variance = self.cantidad_afectada is not None and self.tipo_accion is not None

        if not has_count and not has_variance:
            raise ValueError(
                "Must provide either 'stock_fisico_contado' (physical count mode) "
                "or both 'cantidad_afectada' and 'tipo_accion' (variance mode)."
            )
        return self


class AuditEntryResult(BaseModel):
    client_uuid: str
    id_articulo: str
    stock_real: int
    stock_fisico_contado: Optional[int] = None
    delta_stock: int
    tipo_accion: TipoAccion
    cantidad_afectada: int
    audit_quantity: int
    monto_valorizado: Decimal
    audit_id: Optional[int] = None


class AuditBatchInput(BaseModel):
    items: List[AuditEntryRequest]


class AuditBatchResult(BaseModel):
    results: List[AuditEntryResult]
    total_processed: int
    duplicates_skipped: int
