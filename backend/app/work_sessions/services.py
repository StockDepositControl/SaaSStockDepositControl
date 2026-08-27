from datetime import datetime, time
from typing import Optional
from backend.app.work_sessions.models import WorkSession, WorkSessionCreate
from backend.app.work_sessions.ports import WorkSessionRepositoryPort

class WorkSessionService:
    def __init__(self, repository: WorkSessionRepositoryPort):
        self.repository = repository

    async def get_active_session_id(self, branch_id: int) -> Optional[int]:
        """
        Retrieves the ID of the currently active WorkSession for a given branch.
        """
        return await self.repository.get_active_session_id(branch_id=branch_id)

    async def get_or_create_active_session(
        self, tenant_id: str, branch_id: int, current_dt: Optional[datetime] = None
    ) -> WorkSession:
        """
        Ensures a WorkSession exists for the current day. 
        If one does not exist, it creates a new 24-hour session.
        """
        if current_dt is None:
            current_dt = datetime.utcnow()
            
        # Ensure we work with naive datetimes as per DB conventions
        naive_dt = current_dt.replace(tzinfo=None) if current_dt.tzinfo else current_dt
        
        # Calculate start and end of the day
        start_of_day = datetime.combine(naive_dt.date(), time.min)
        end_of_day = datetime.combine(naive_dt.date(), time.max)
        
        session = await self.repository.get_active_session(
            tenant_id=tenant_id, 
            branch_id=branch_id, 
            target_date=naive_dt
        )

        if session:
            return session

        new_session = WorkSessionCreate(
            tenant_id=tenant_id,
            branch_id=branch_id,
            opened_at=start_of_day,
            closed_at=end_of_day,
            status="OPEN"
        )
        return await self.repository.create_session(new_session)
