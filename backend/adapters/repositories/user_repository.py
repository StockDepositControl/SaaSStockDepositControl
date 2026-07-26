from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.app.users.models import User
from backend.app.users.ports import UserRepositoryPort
from backend.adapters.repositories.models import Usuario
from backend.adapters.database.multi_tenant import get_tenant_id

class SQLAlchemyUserRepository(UserRepositoryPort):
    """
    SQLAlchemy 2.0 implementation of UserRepositoryPort.
    Queries the users database table (`usuarios`) with tenant isolation.
    """
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def get_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        active_tenant = tenant_id or get_tenant_id()
        async with self.session_factory() as session:
            stmt = select(Usuario).where(
                Usuario.tenant_id == active_tenant,
                Usuario.email == email,
                Usuario.is_active == True
            )
            result = await session.execute(stmt)
            usuario_orm = result.scalar_one_or_none()
            if not usuario_orm:
                return None
            return User.model_validate(usuario_orm)

    async def get_by_id(self, tenant_id: str, id_usuario: int) -> Optional[User]:
        active_tenant = tenant_id or get_tenant_id()
        async with self.session_factory() as session:
            stmt = select(Usuario).where(
                Usuario.tenant_id == active_tenant,
                Usuario.id_usuario == id_usuario,
                Usuario.is_active == True
            )
            result = await session.execute(stmt)
            usuario_orm = result.scalar_one_or_none()
            if not usuario_orm:
                return None
            return User.model_validate(usuario_orm)

    async def get_password_hash(self, tenant_id: str, email: str) -> Optional[str]:
        active_tenant = tenant_id or get_tenant_id()
        async with self.session_factory() as session:
            stmt = select(Usuario.password_hash).where(
                Usuario.tenant_id == active_tenant,
                Usuario.email == email,
                Usuario.is_active == True
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
