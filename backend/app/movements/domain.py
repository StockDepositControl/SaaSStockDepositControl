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
