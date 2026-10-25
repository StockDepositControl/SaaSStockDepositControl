from typing import Optional

from pydantic import BaseModel, ConfigDict


class BranchBase(BaseModel):
    description: str


class BranchCreate(BranchBase):
    tenant_id: int


class BranchUpdate(BaseModel):
    description: Optional[str] = None


class Branch(BranchBase):
    id_branch: int
    tenant_id: int

    model_config = ConfigDict(from_attributes=True)
