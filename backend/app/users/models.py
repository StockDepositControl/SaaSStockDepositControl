from enum import Enum
from typing import List, Optional
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
    tenant_id: int
    first_name: str
    last_name: str
    email: str
    branch_id: Optional[int] = None
    is_active: bool = True
    roles: List[UserRole] = []

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    branch_id: Optional[int] = None
    is_active: Optional[bool] = None
    roles: Optional[List[UserRole]] = None
    password: Optional[str] = None

class User(UserBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)
