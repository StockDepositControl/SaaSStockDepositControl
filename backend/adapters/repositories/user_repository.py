from typing import Optional
from sqlalchemy import select
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

    def _to_domain(self, tenant_id: str, user_orm: UserORM) -> User:
        # Determine role from ORM roles list if available, default to ADMINISTRADOR
        role_name = UserRole.ADMINISTRADOR
        if user_orm.roles:
            r_name = user_orm.roles[0].name.lower()
            if r_name in [r.value for r in UserRole]:
                role_name = UserRole(r_name)

        return User(
            id_usuario=user_orm.user_id,
            tenant_id=tenant_id,
            nombre_completo=f"{user_orm.first_name} {user_orm.last_name}".strip(),
            email=user_orm.email,
            rol=role_name,
            id_sucursal=user_orm.branch_id or 1
        )

    async def get_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        active_tenant = tenant_id or get_tenant_id()
        async with self.session_factory() as session:
            stmt = select(UserORM).where(
                UserORM.email == email,
                UserORM.is_active == True
            )
            result = await session.execute(stmt)
            user_orm = result.scalar_one_or_none()
            if not user_orm:
                return None
            return self._to_domain(active_tenant, user_orm)

    async def get_by_id(self, tenant_id: str, id_usuario: int) -> Optional[User]:
        active_tenant = tenant_id or get_tenant_id()
        async with self.session_factory() as session:
            stmt = select(UserORM).where(
                UserORM.user_id == id_usuario,
                UserORM.is_active == True
            )
            result = await session.execute(stmt)
            user_orm = result.scalar_one_or_none()
            if not user_orm:
                return None
            return self._to_domain(active_tenant, user_orm)

    async def get_password_hash(self, tenant_id: str, email: str) -> Optional[str]:
        async with self.session_factory() as session:
            stmt = select(UserORM.password_hash).where(
                UserORM.email == email,
                UserORM.is_active == True
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
