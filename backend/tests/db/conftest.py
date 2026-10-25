import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.adapters.repositories.models import BaseArticles, BaseUsers, BaseAnalytics

URL_ARTICLES = "sqlite+aiosqlite:///file:test_articles?mode=memory&cache=shared&uri=true"
URL_USERS = "sqlite+aiosqlite:///file:test_users?mode=memory&cache=shared&uri=true"
URL_ANALYTICS = "sqlite+aiosqlite:///file:test_analytics?mode=memory&cache=shared&uri=true"


@pytest_asyncio.fixture
async def db_engines():
    engine_articles = create_async_engine(URL_ARTICLES, echo=False)
    engine_users = create_async_engine(URL_USERS, echo=False)
    engine_analytics = create_async_engine(URL_ANALYTICS, echo=False)

    async with engine_articles.begin() as conn:
        await conn.run_sync(BaseArticles.metadata.create_all)
    async with engine_users.begin() as conn:
        await conn.run_sync(BaseUsers.metadata.create_all)
    async with engine_analytics.begin() as conn:
        await conn.run_sync(BaseAnalytics.metadata.create_all)

    yield {
        "articles": engine_articles,
        "users": engine_users,
        "analytics": engine_analytics,
        "url_articles": URL_ARTICLES,
        "url_users": URL_USERS,
        "url_analytics": URL_ANALYTICS,
    }

    await engine_articles.dispose()
    await engine_users.dispose()
    await engine_analytics.dispose()


@pytest_asyncio.fixture
async def async_db_engine(db_engines):
    yield db_engines["articles"]


@pytest_asyncio.fixture
async def async_sessions(db_engines):
    factory_articles = async_sessionmaker(bind=db_engines["articles"], expire_on_commit=False, class_=AsyncSession)
    factory_users = async_sessionmaker(bind=db_engines["users"], expire_on_commit=False, class_=AsyncSession)
    factory_analytics = async_sessionmaker(bind=db_engines["analytics"], expire_on_commit=False, class_=AsyncSession)

    async with factory_articles() as s_articles, factory_users() as s_users, factory_analytics() as s_analytics:
        yield {
            "articles": s_articles,
            "users": s_users,
            "analytics": s_analytics,
        }


@pytest_asyncio.fixture
async def async_session(async_sessions):
    yield async_sessions["articles"]


DB_ENV_VARS = [
    "ARTICLES_DATABASE_URL",
    "USERS_DATABASE_URL",
    "ANALYTICS_DATABASE_URL",
    "DATABASE_URL",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME_ARTICLES",
    "DB_NAME_USERS",
    "DB_NAME_ANALYTICS",
    "DB_SSL_MODE",
    "DB_SSL_CA",
]


@pytest.fixture
def clean_db_env(monkeypatch):
    """Removes database-related env vars so URL/TLS resolution tests start from a blank slate."""
    for name in DB_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
