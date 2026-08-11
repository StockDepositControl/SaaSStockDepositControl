from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class FamiliaBase(BaseModel):
    des_familia: str

class FamiliaCreate(FamiliaBase):
    pass

class FamiliaUpdate(BaseModel):
    des_familia: Optional[str] = None

class Familia(FamiliaBase):
    id_familia: str

    model_config = ConfigDict(from_attributes=True)


class GrupoBase(BaseModel):
    id_familia: str
    id_grupo: str
    des_grupo: str

class GrupoCreate(GrupoBase):
    pass

class GrupoUpdate(BaseModel):
    des_grupo: Optional[str] = None

class Grupo(GrupoBase):
    model_config = ConfigDict(from_attributes=True)


class MarcaBase(BaseModel):
    des_marca: str

class MarcaCreate(MarcaBase):
    pass

class MarcaUpdate(BaseModel):
    des_marca: Optional[str] = None

class Marca(MarcaBase):
    id_marca: int

    model_config = ConfigDict(from_attributes=True)


class ArticuloBase(BaseModel):
    id_articulo: str
    presentacion: Optional[str] = None
    des_articulo: str
    id_marca: Optional[int] = None
    des_marca: Optional[str] = None
    id_familia: Optional[str] = None
    des_familia: Optional[str] = None
    id_grupo: Optional[str] = None
    des_grupo: Optional[str] = None
    pcio_com_siva: Decimal
    fue_auditado: bool = False

class ArticuloCreate(ArticuloBase):
    pass

class ArticuloUpdate(BaseModel):
    presentacion: Optional[str] = None
    des_articulo: Optional[str] = None
    id_marca: Optional[int] = None
    des_marca: Optional[str] = None
    id_familia: Optional[str] = None
    des_familia: Optional[str] = None
    id_grupo: Optional[str] = None
    des_grupo: Optional[str] = None
    pcio_com_siva: Optional[Decimal] = None

class Articulo(ArticuloBase):
    model_config = ConfigDict(from_attributes=True)


class ArticuloPublicOut(BaseModel):
    id_articulo: str
    presentacion: Optional[str] = None
    des_articulo: str
    id_marca: Optional[int] = None
    des_marca: Optional[str] = None
    id_familia: Optional[str] = None
    des_familia: Optional[str] = None
    id_grupo: Optional[str] = None
    des_grupo: Optional[str] = None
    fue_auditado: bool = False

    model_config = ConfigDict(from_attributes=True)


class ArticuloAdminOut(ArticuloPublicOut):
    pcio_com_siva: Decimal


