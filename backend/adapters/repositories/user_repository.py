from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.app.users.models import User, UserRole
from backend.app.users.ports import UserRepositoryPort
from backend.adapters.repositories.models import User as UserORM
from backend.adapters.database.connection import get_users_session_factory
from backend.adapters.database.multi_tenant import get_tenant_id

class SQLAlchemyUserRepository(UserRepositoryPort):
    """
    SQLAlchemy 2.0 implementation of UserRepositoryPort.
    Queries the users database table (`users`) in db_users with tenant isolation.
    """
    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_users_session_factory()

    def _to_domain(self, user_orm: UserORM) -> User:
        roles: list[UserRole] = []
        if user_orm.roles:
            for r in user_orm.roles:
                r_name = r.name.lower()
                if r_name in [ur.value for ur in UserRole]:
                    roles.append(UserRole(r_name))

        return User(
            user_id=user_orm.user_id,
            tenant_id=user_orm.tenant_id,
            first_name=user_orm.first_name,
            last_name=user_orm.last_name,
            email=user_orm.email,
            roles=roles,
            branch_id=user_orm.branch_id,
            is_active=user_orm.is_active,
        )

    async def get_by_email(self, email: str, tenant_id: Optional[int] = None) -> Optional[User]:
        active_tenant = tenant_id if tenant_id is not None else (int(get_tenant_id()) if get_tenant_id() else None)
        async with self.session_factory() as session:
            conditions = [UserORM.email == email, UserORM.is_active == True]
            if active_tenant is not None:
                conditions.append(UserORM.tenant_id == active_tenant)

            stmt = (
                select(UserORM)
                .options(selectinload(UserORM.roles))
                .where(*conditions)
            )
            result = await session.execute(stmt)
            user_orm = result.scalar_one_or_none()
            if not user_orm:
                return None
            return self._to_domain(user_orm)

    async def get_by_id(self, tenant_id: int, user_id: int) -> Optional[User]:
        async with self.session_factory() as session:
            stmt = (
                select(UserORM)
                .options(selectinload(UserORM.roles))
                .where(
                    UserORM.user_id == user_id,
                    UserORM.tenant_id == tenant_id,
                    UserORM.is_active == True
                )
            )
            result = await session.execute(stmt)
            user_orm = result.scalar_one_or_none()
            if not user_orm:
                return None
            return self._to_domain(user_orm)

    async def get_password_hash(self, email: str, tenant_id: Optional[int] = None) -> Optional[str]:
        active_tenant = tenant_id if tenant_id is not None else (int(get_tenant_id()) if get_tenant_id() else None)
        async with self.session_factory() as session:
            conditions = [UserORM.email == email, UserORM.is_active == True]
            if active_tenant is not None:
                conditions.append(UserORM.tenant_id == active_tenant)

            stmt = select(UserORM.password_hash).where(*conditions)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
