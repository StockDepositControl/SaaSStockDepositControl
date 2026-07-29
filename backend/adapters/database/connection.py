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
    Configured for multi-database layout (db_articles, db_users, db_analytics).
    """
    def __init__(self, database_url: str = None):
        if not database_url:
            database_url = os.getenv("ARTICLES_DATABASE_URL") or os.getenv("DATABASE_URL")
            if not database_url:
                db_user = os.getenv("DB_USER", "root")
                db_pass = os.getenv("DB_PASSWORD", "")
                db_host = os.getenv("DB_HOST", "localhost")
                db_port = os.getenv("DB_PORT", "3306")
                db_name = os.getenv("DB_NAME_ARTICLES", "db_articles")
                database_url = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        
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
        """Disposes of connection pool resources across all multi-db pools."""
        await self.engine.dispose()
        global _articles_engine, _users_engine, _analytics_engine
        if _articles_engine is not None:
            await _articles_engine.dispose()
        if _users_engine is not None:
            await _users_engine.dispose()
        if _analytics_engine is not None:
            await _analytics_engine.dispose()


_articles_engine = None
_articles_session_factory = None

_users_engine = None
_users_session_factory = None

_analytics_engine = None
_analytics_session_factory = None


def get_articles_session_factory() -> async_sessionmaker:
    """Returns the session factory for db_articles."""
    global _articles_engine, _articles_session_factory
    if _articles_session_factory is None:
        database_url = os.getenv("ARTICLES_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not database_url:
            db_user = os.getenv("DB_USER", "root")
            db_pass = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "3306")
            db_name = os.getenv("DB_NAME_ARTICLES", "db_articles")
            database_url = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        _articles_engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True
        )
        _articles_session_factory = async_sessionmaker(
            bind=_articles_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
    return _articles_session_factory


def get_users_session_factory() -> async_sessionmaker:
    """Returns the session factory for db_users."""
    global _users_engine, _users_session_factory
    if _users_session_factory is None:
        database_url = os.getenv("USERS_DATABASE_URL")
        if not database_url:
            db_user = os.getenv("DB_USER", "root")
            db_pass = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "3306")
            db_name = os.getenv("DB_NAME_USERS", "db_users")
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


def get_analytics_session_factory() -> async_sessionmaker:
    """Returns the session factory for db_analytics."""
    global _analytics_engine, _analytics_session_factory
    if _analytics_session_factory is None:
        database_url = os.getenv("ANALYTICS_DATABASE_URL")
        if not database_url:
            db_user = os.getenv("DB_USER", "root")
            db_pass = os.getenv("DB_PASSWORD", "")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "3306")
            db_name = os.getenv("DB_NAME_ANALYTICS", "db_analytics")
            database_url = f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        _analytics_engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True
        )
        _analytics_session_factory = async_sessionmaker(
            bind=_analytics_engine,
            expire_on_commit=False,
            class_=AsyncSession
        )
    return _analytics_session_factory
