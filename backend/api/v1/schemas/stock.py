from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

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
