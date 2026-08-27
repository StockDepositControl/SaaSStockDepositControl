from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.app.work_sessions.models import WorkSession, WorkSessionCreate
from backend.app.work_sessions.ports import WorkSessionRepositoryPort
from backend.adapters.repositories.models.analytics import WorkSession as WorkSessionORM
from backend.adapters.database.connection import get_analytics_session_factory

class SQLAlchemyWorkSessionRepository(WorkSessionRepositoryPort):
    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_analytics_session_factory()

    def _to_domain(self, orm_model: WorkSessionORM) -> WorkSession:
        return WorkSession(
            session_id=orm_model.session_id,
            tenant_id=orm_model.tenant_id,
            branch_id=orm_model.branch_id,
            opened_at=orm_model.opened_at,
            closed_at=orm_model.closed_at,
            status=orm_model.status,
            created_at=orm_model.created_at,
        )

    async def get_active_session(self, tenant_id: str, branch_id: int, target_date: datetime) -> Optional[WorkSession]:
        async with self.session_factory() as session:
            stmt = (
                select(WorkSessionORM)
                .where(
                    WorkSessionORM.tenant_id == tenant_id,
                    WorkSessionORM.branch_id == branch_id,
                    WorkSessionORM.opened_at <= target_date,
                    WorkSessionORM.closed_at >= target_date,
                    WorkSessionORM.status == "OPEN"
                )
                .order_by(WorkSessionORM.opened_at.desc())
            )
            result = await session.execute(stmt)
            orm_model = result.scalar_one_or_none()
            if not orm_model:
                return None
            return self._to_domain(orm_model)

    async def get_active_session_id(self, branch_id: int) -> Optional[int]:
        async with self.session_factory() as session:
            stmt = (
                select(WorkSessionORM.session_id)
                .where(
                    WorkSessionORM.branch_id == branch_id,
                    WorkSessionORM.status == "OPEN"
                )
                .order_by(WorkSessionORM.opened_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_session(self, session: WorkSessionCreate) -> WorkSession:
        async with self.session_factory() as db_session:
            new_orm = WorkSessionORM(
                tenant_id=session.tenant_id,
                branch_id=session.branch_id,
                opened_at=session.opened_at,
                closed_at=session.closed_at,
                status=session.status,
            )
            db_session.add(new_orm)
            await db_session.commit()
            await db_session.refresh(new_orm)
            return self._to_domain(new_orm)
