from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
from backend.app.work_sessions.models import WorkSession, WorkSessionCreate

class WorkSessionRepositoryPort(ABC):
    """
    Abstract port for WorkSession data access.
    Pure domain interface decoupled from SQL/ORM.
    """
    @abstractmethod
    async def get_active_session(self, tenant_id: str, branch_id: int, target_date: datetime) -> Optional[WorkSession]:
        """
        Retrieves the active WorkSession for a tenant/branch covering the target date.
        """
        pass

    @abstractmethod
    async def create_session(self, session: WorkSessionCreate) -> WorkSession:
        """
        Creates a new WorkSession.
        """
        pass
