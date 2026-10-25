from datetime import datetime

import pytest
from backend.app.work_sessions.models import WorkSession, WorkSessionCreate
from backend.app.work_sessions.ports import WorkSessionRepositoryPort
from backend.app.work_sessions.services import WorkSessionService


class MockWorkSessionRepository(WorkSessionRepositoryPort):
    def __init__(self):
        self.sessions = []

    async def get_active_session(
        self, tenant_id: str, branch_id: int, target_date: datetime
    ):
        for s in self.sessions:
            if (
                s.tenant_id == tenant_id
                and s.branch_id == branch_id
                and s.opened_at <= target_date <= s.closed_at
            ):
                return s
        return None

    async def get_active_session_id(self, branch_id: int):
        for s in reversed(self.sessions):
            if s.branch_id == branch_id and s.status == "OPEN":
                return s.session_id
        return None

    async def create_session(self, session: WorkSessionCreate):
        new_session = WorkSession(
            session_id=len(self.sessions) + 1,
            tenant_id=session.tenant_id,
            branch_id=session.branch_id,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
            status=session.status,
            created_at=datetime.utcnow(),
        )
        self.sessions.append(new_session)
        return new_session


@pytest.mark.asyncio
async def test_get_or_create_active_session_creates_new():
    repo = MockWorkSessionRepository()
    service = WorkSessionService(repository=repo)

    current_dt = datetime(2023, 10, 10, 14, 30)
    session = await service.get_or_create_active_session(
        tenant_id=1, branch_id=1, current_dt=current_dt
    )

    assert session is not None
    assert session.session_id == 1
    assert session.opened_at.hour == 0
    assert session.opened_at.minute == 0
    assert session.closed_at.hour == 23
    assert session.closed_at.minute == 59
    assert session.closed_at.second == 59


@pytest.mark.asyncio
async def test_get_or_create_active_session_returns_existing():
    repo = MockWorkSessionRepository()
    service = WorkSessionService(repository=repo)

    current_dt = datetime(2023, 10, 10, 14, 30)
    session1 = await service.get_or_create_active_session(
        tenant_id=1, branch_id=1, current_dt=current_dt
    )

    current_dt2 = datetime(2023, 10, 10, 18, 45)
    session2 = await service.get_or_create_active_session(
        tenant_id=1, branch_id=1, current_dt=current_dt2
    )

    assert session1.session_id == session2.session_id
    assert len(repo.sessions) == 1
