import asyncio
import logging
import os
import ssl
from contextlib import asynccontextmanager
from typing import AsyncIterator
from urllib.parse import quote

from backend.app.ports.database import ConnectionProvider, DatabaseSession
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure environment is loaded
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConfigError(ValueError):
    """Raised when database environment configuration is invalid."""


# target -> (specific URL env var, database-name env var, default database name)
_DB_TARGETS = {
    "articles": ("ARTICLES_DATABASE_URL", "DB_NAME_ARTICLES", "db_articles"),
    "users": ("USERS_DATABASE_URL", "DB_NAME_USERS", "db_users"),
    "analytics": ("ANALYTICS_DATABASE_URL", "DB_NAME_ANALYTICS", "db_analytics"),
}

_SSL_MODES = ("disable", "require", "verify-ca")


def resolve_database_url(target: str) -> str:
    """
    Resolves the URL for a logical database with a fixed precedence:
    1. Specific URL (``<TARGET>_DATABASE_URL``)
    2. ``DATABASE_URL`` (verbatim for articles, database name substituted otherwise)
    3. ``DB_*`` component variables
    """
    if target not in _DB_TARGETS:
        raise DatabaseConfigError(f"Unknown database target: {target!r}")
    url_var, name_var, default_name = _DB_TARGETS[target]
    db_name = os.getenv(name_var, default_name)

    specific_url = os.getenv(url_var)
    if specific_url:
        return specific_url

    base_url = os.getenv("DATABASE_URL")
    if base_url:
        if target == "articles":
            return base_url
        return (
            make_url(base_url)
            .set(database=db_name)
            .render_as_string(hide_password=False)
        )

    # quote (not quote_plus): SQLAlchemy decodes with unquote, so a space must stay %20.
    db_user = quote(os.getenv("DB_USER", "root"), safe="")
    db_pass = quote(os.getenv("DB_PASSWORD", ""), safe="")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    return f"mysql+aiomysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


def build_ssl_connect_args() -> dict:
    """
    Builds aiomysql ``connect_args`` from ``DB_SSL_MODE`` / ``DB_SSL_CA``.
    ``disable`` (default) yields no args; ``require`` encrypts without verifying
    the server certificate; ``verify-ca`` also validates it against ``DB_SSL_CA``
    (or the system trust store when unset). Hostname is not checked in either mode.
    """
    mode = os.getenv("DB_SSL_MODE", "disable").strip().lower()
    if mode not in _SSL_MODES:
        raise DatabaseConfigError(
            f"Invalid DB_SSL_MODE {mode!r}; expected one of {', '.join(_SSL_MODES)}"
        )
    if mode == "disable":
        return {}

    if mode == "require":
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return {"ssl": context}

    ca_path = os.getenv("DB_SSL_CA") or None
    try:
        context = ssl.create_default_context(cafile=ca_path)
    except (OSError, ssl.SSLError) as exc:
        raise DatabaseConfigError(f"Cannot load DB_SSL_CA {ca_path!r}: {exc}") from exc
    context.check_hostname = False
    return {"ssl": context}


def _create_engine(database_url: str):
    kwargs = {"echo": False, "pool_pre_ping": True}
    connect_args = build_ssl_connect_args()
    if connect_args:
        kwargs["connect_args"] = connect_args
    return create_async_engine(database_url, **kwargs)


async def _probe(get_factory) -> bool:
    """
    Runs SELECT 1 through a session factory; any failure (config or I/O) is a miss.
    """
    try:
        async with get_factory()() as raw_session:
            await raw_session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database health probe failed: %s", type(exc).__name__)
        return False


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
            database_url = resolve_database_url("articles")

        self.engine = _create_engine(database_url)
        self.session_factory = async_sessionmaker(
            bind=self.engine, expire_on_commit=False, class_=AsyncSession
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
        Lightweight connectivity probe using SELECT 1 on all three logical databases.
        Returns True only if every database responds, False otherwise.
        """
        return all((await self.check_databases()).values())

    async def check_databases(self) -> dict[str, bool]:
        factories = {
            "articles": lambda: self.session_factory,
            "users": get_users_session_factory,
            "analytics": get_analytics_session_factory,
        }
        results = await asyncio.gather(
            *(_probe(factory) for factory in factories.values())
        )
        return dict(zip(factories, results))

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
        _articles_engine = _create_engine(resolve_database_url("articles"))
        _articles_session_factory = async_sessionmaker(
            bind=_articles_engine, expire_on_commit=False, class_=AsyncSession
        )
    return _articles_session_factory


def get_users_session_factory() -> async_sessionmaker:
    """Returns the session factory for db_users."""
    global _users_engine, _users_session_factory
    if _users_session_factory is None:
        _users_engine = _create_engine(resolve_database_url("users"))
        _users_session_factory = async_sessionmaker(
            bind=_users_engine, expire_on_commit=False, class_=AsyncSession
        )
    return _users_session_factory


def get_analytics_session_factory() -> async_sessionmaker:
    """Returns the session factory for db_analytics."""
    global _analytics_engine, _analytics_session_factory
    if _analytics_session_factory is None:
        _analytics_engine = _create_engine(resolve_database_url("analytics"))
        _analytics_session_factory = async_sessionmaker(
            bind=_analytics_engine, expire_on_commit=False, class_=AsyncSession
        )
    return _analytics_session_factory
