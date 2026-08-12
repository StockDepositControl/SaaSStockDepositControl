from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.app.branches.models import Branch as BranchDomain, BranchCreate, BranchUpdate
from backend.app.branches.ports import BranchRepositoryPort
from backend.adapters.repositories.models.users import Branch as BranchORM
from backend.adapters.database.connection import get_users_session_factory

class SQLAlchemyBranchRepository(BranchRepositoryPort):
    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_users_session_factory()

    def _to_domain(self, orm: BranchORM) -> BranchDomain:
        return BranchDomain(
            id_branch=orm.id_branch,
            tenant_id=orm.tenant_id,
            description=orm.description
        )

    async def get_by_id(self, branch_id: int) -> Optional[BranchDomain]:
        async with self.session_factory() as session:
            stmt = select(BranchORM).where(BranchORM.id_branch == branch_id)
            result = await session.execute(stmt)
            orm = result.scalar_one_or_none()
            return self._to_domain(orm) if orm else None

    async def list_by_tenant(self, tenant_id: int) -> List[BranchDomain]:
        async with self.session_factory() as session:
            stmt = select(BranchORM).where(BranchORM.tenant_id == tenant_id)
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]

    async def create(self, data: BranchCreate) -> BranchDomain:
        async with self.session_factory() as session:
            async with session.begin():
                orm = BranchORM(
                    tenant_id=data.tenant_id,
                    description=data.description
                )
                session.add(orm)
            await session.refresh(orm)
            return self._to_domain(orm)

    async def update(self, branch_id: int, data: BranchUpdate) -> Optional[BranchDomain]:
        async with self.session_factory() as session:
            async with session.begin():
                stmt = select(BranchORM).where(BranchORM.id_branch == branch_id)
                result = await session.execute(stmt)
                orm = result.scalar_one_or_none()
                if not orm:
                    return None
                if data.description is not None:
                    orm.description = data.description
            await session.refresh(orm)
            return self._to_domain(orm)

    async def delete(self, branch_id: int) -> bool:
        async with self.session_factory() as session:
            async with session.begin():
                stmt = select(BranchORM).where(BranchORM.id_branch == branch_id)
                result = await session.execute(stmt)
                orm = result.scalar_one_or_none()
                if not orm:
                    return False
                await session.delete(orm)
            return True
