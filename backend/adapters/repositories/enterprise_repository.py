from typing import List, Optional

from backend.adapters.database.connection import get_users_session_factory
from backend.adapters.repositories.models.users import Enterprise as EnterpriseORM
from backend.app.enterprises.models import Enterprise as EnterpriseDomain
from backend.app.enterprises.models import EnterpriseCreate, EnterpriseUpdate
from backend.app.enterprises.ports import EnterpriseRepositoryPort
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker


class SQLAlchemyEnterpriseRepository(EnterpriseRepositoryPort):
    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_users_session_factory()

    def _to_domain(self, orm: EnterpriseORM) -> EnterpriseDomain:
        return EnterpriseDomain(tenant_id=orm.tenant_id, description=orm.description)

    async def get_by_id(self, tenant_id: int) -> Optional[EnterpriseDomain]:
        async with self.session_factory() as session:
            stmt = select(EnterpriseORM).where(EnterpriseORM.tenant_id == tenant_id)
            result = await session.execute(stmt)
            orm = result.scalar_one_or_none()
            return self._to_domain(orm) if orm else None

    async def list_all(self) -> List[EnterpriseDomain]:
        async with self.session_factory() as session:
            stmt = select(EnterpriseORM)
            result = await session.execute(stmt)
            return [self._to_domain(orm) for orm in result.scalars().all()]

    async def create(self, data: EnterpriseCreate) -> EnterpriseDomain:
        async with self.session_factory() as session:
            async with session.begin():
                orm = EnterpriseORM(
                    tenant_id=data.tenant_id, description=data.description
                )
                session.add(orm)
            await session.refresh(orm)
            return self._to_domain(orm)

    async def update(
        self, tenant_id: int, data: EnterpriseUpdate
    ) -> Optional[EnterpriseDomain]:
        async with self.session_factory() as session:
            async with session.begin():
                stmt = select(EnterpriseORM).where(EnterpriseORM.tenant_id == tenant_id)
                result = await session.execute(stmt)
                orm = result.scalar_one_or_none()
                if not orm:
                    return None
                if data.description is not None:
                    orm.description = data.description
            await session.refresh(orm)
            return self._to_domain(orm)

    async def delete(self, tenant_id: int) -> bool:
        async with self.session_factory() as session:
            async with session.begin():
                stmt = select(EnterpriseORM).where(EnterpriseORM.tenant_id == tenant_id)
                result = await session.execute(stmt)
                orm = result.scalar_one_or_none()
                if not orm:
                    return False
                await session.delete(orm)
            return True
