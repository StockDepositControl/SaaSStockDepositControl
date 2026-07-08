from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TipoAccion(str, Enum):
    ALTA = "Alta"
    BAJA = "Baja"
    SIN_ACCION = "Sin Acción"

class StockPorDepositoBase(BaseModel):
    tenant_id: str
    id_sucursal: int
    id_deposito: int
    id_articulo: str
    stock_real: int
    fue_auditado: bool
    fecha_hora_auditacion: Optional[datetime] = None

class StockPorDepositoCreate(StockPorDepositoBase):
    pass

class StockPorDepositoUpdate(BaseModel):
    stock_real: Optional[int] = None
    fue_auditado: Optional[bool] = None
    fecha_hora_auditacion: Optional[datetime] = None

class StockPorDeposito(StockPorDepositoBase):
    model_config = ConfigDict(from_attributes=True)


class LotePorDepositoBase(BaseModel):
    tenant_id: str
    id_deposito: int
    id_articulo: str
    lote: str
    vencimiento: date
    stock_real: int

class LotePorDepositoCreate(LotePorDepositoBase):
    pass

class LotePorDepositoUpdate(BaseModel):
    vencimiento: Optional[date] = None
    stock_real: Optional[int] = None

class LotePorDeposito(LotePorDepositoBase):
    model_config = ConfigDict(from_attributes=True)


class AuditoriaRegistroBase(BaseModel):
    tenant_id: str
    id_sucursal: int
    id_deposito: int
    id_articulo: str
    tipo_accion: TipoAccion
    cantidad_afectada: int
    monto_valorizado: Decimal
    id_usuario: int
    fecha_hora: datetime

class AuditoriaRegistroCreate(AuditoriaRegistroBase):
    pass

class AuditoriaRegistro(AuditoriaRegistroBase):
    id_auditoria: int

    model_config = ConfigDict(from_attributes=True)
