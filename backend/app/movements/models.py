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
    fue_auditado: bool = False
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
    client_uuid: Optional[str] = None
    observation: Optional[str] = None
    audit_action_type: Optional[str] = None

class AuditoriaRegistroCreate(AuditoriaRegistroBase):
    pass

class AuditoriaRegistro(AuditoriaRegistroBase):
    id_auditoria: int

    model_config = ConfigDict(from_attributes=True)


class AuditEntryInput(BaseModel):
    id_sucursal: Optional[int] = None
    id_deposito: Optional[int] = None
    id_articulo: str
    stock_fisico_contado: int
    observation: Optional[str] = None
    audit_action_type: Optional[str] = None


class AuditEntryResult(BaseModel):
    client_uuid: str
    id_articulo: str
    stock_real: int
    stock_fisico_contado: int
    delta_stock: int
    tipo_accion: TipoAccion
    cantidad_afectada: int
    monto_valorizado: Decimal
    id_auditoria: Optional[int] = None


class AuditBatchInput(BaseModel):
    items: list[AuditEntryInput]


class AuditBatchResult(BaseModel):
    results: list[AuditEntryResult]
    total_processed: int
    duplicates_skipped: int


class ArticleStockPositionPublicOut(BaseModel):
    des_articulo: str
    presentacion: Optional[str] = None
    des_marca: Optional[str] = None
    des_familia: Optional[str] = None
    des_grupo: Optional[str] = None
    
    id_sucursal: int
    id_deposito: int
    stock_real: int


class ArticleStockPositionAdminOut(ArticleStockPositionPublicOut):
    pcio_com_siva: Decimal
