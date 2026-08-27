from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class WorkSessionBase(BaseModel):
    tenant_id: int
    branch_id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    status: str = "OPEN"

class WorkSessionCreate(WorkSessionBase):
    pass

class WorkSession(WorkSessionBase):
    session_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
