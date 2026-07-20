from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserRole(str, Enum):
    ADMINISTRADOR = "administrador"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"

class AuthToken(BaseModel):
    access_token: str
    token_type: str

class LoginCredentials(BaseModel):
    email: str
    password: str

class UserBase(BaseModel):
    tenant_id: str
    nombre_completo: str
    email: str
    rol: UserRole
    id_sucursal: int

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[UserRole] = None
    id_sucursal: Optional[int] = None
    password: Optional[str] = None

class User(UserBase):
    id_usuario: int

    model_config = ConfigDict(from_attributes=True)
