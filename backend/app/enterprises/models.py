from typing import Optional

from pydantic import BaseModel, ConfigDict


class EnterpriseBase(BaseModel):
    description: str


class EnterpriseCreate(EnterpriseBase):
    tenant_id: int


class EnterpriseUpdate(BaseModel):
    description: Optional[str] = None


class Enterprise(EnterpriseBase):
    tenant_id: int

    model_config = ConfigDict(from_attributes=True)
