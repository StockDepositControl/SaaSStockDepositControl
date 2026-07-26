import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Any
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.ports.database import ConnectionProvider, DatabaseSession

# Ensure environment is loaded
load_dotenv()

class SQLAlchemyDatabaseSession(DatabaseSession):
    """
    SQLAlchemy-specific concrete implementation of the DatabaseSession port.
    """
    def __init__(self, session: AsyncSession):
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    @property
    def raw_session(self) -> AsyncSession:
        return self._session


class SQLAlchemyConnectionProvider(ConnectionProvider):
    """
    SQLAlchemy-specific concrete implementation of the ConnectionProvider port.
    Configured for Phase 1 (single tenant MariaDB instance).
    """
    def __init__(self, database_url: str = None):
        if not database_url:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                db_user = os.getenv("DB_USER", "root")
                db_pass = os.getenv("DB_PASSWORD", "")
                db_host = os.getenv("DB_HOST", "localhost")
                db_port = os.getenv("DB_PORT", "3306")
                db_name = os.getenv("DB_NAME", "stock_deposit_control")
                database_url = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        
        # Phase 1: Establish connection pool targeting single client instance
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[DatabaseSession]:
        """
        Asynchronously yields a transaction-scoped DatabaseSession.
        
        🚀 PHASE 2 MULTI-TENANT HOOK:
        -----------------------------
        In Phase 2 (dynamic database-per-tenant selection), we will hook into this method
        to swap the connection pool (engine/sessionmaker) dynamically.
        
        Example implementation path:
        1. Extract the active tenant identifier from request context (e.g. via ContextVars):
           from backend.api.middlewares.tenant_context import active_tenant
           tenant_id = active_tenant.get()
           
        2. Look up or retrieve a cached engine from a dynamic tenant engine registry:
           tenant_engine = self.registry.get_engine(tenant_id)
           
        3. Create and bind the AsyncSession to the dynamically-swapped engine:
           async with AsyncSession(bind=tenant_engine, expire_on_commit=False) as raw_session:
               yield SQLAlchemyDatabaseSession(raw_session)
        """
        async with self.session_factory() as raw_session:
            try:
                yield SQLAlchemyDatabaseSession(raw_session)
            except Exception:
                await raw_session.rollback()
                raise
            finally:
                await raw_session.close()

    async def check_connectivity(self) -> bool:
        """
        Lightweight connectivity probe using SELECT 1.
        Returns True if the database responds, False otherwise.
        """
        try:
            from sqlalchemy import text
            async with self.session_factory() as raw_session:
                await raw_session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def dispose(self) -> None:
        """Disposes of connection pool resources."""
        await self.engine.dispose()
        global _users_engine
        if _users_engine is not None:
            await _users_engine.dispose()


_users_engine = None
_users_session_factory = None

def get_users_session_factory() -> async_sessionmaker:
    """
    Returns the session factory for the Users & Auth database (engine_users).
    Phase 1: Uses USERS_DATABASE_URL (falls back to DATABASE_URL or DB_* environment variables).
    """
    global _users_engine, _users_session_factory
    if _users_session_factory is None:
        database_url = os.getenv("USERS_DATABASE_URL")
        if not database_url:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                db_user = os.getenv("DB_USER", "root")
                db_pass = os.getenv("DB_PASSWORD", "")
                db_host = os.getenv("DB_HOST", "localhost")
                db_port = os.getenv("DB_PORT", "3306")
                db_name = os.getenv("DB_NAME", "stock_deposit_control")
                database_url = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        _users_engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True
        )
        _users_session_factory = async_sessionmaker(
            bind=_users_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
    return _users_session_factory

