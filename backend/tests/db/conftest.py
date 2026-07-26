import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.adapters.repositories.models import Base

@pytest_asyncio.fixture
async def async_db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_db_engine):
    session_factory = async_sessionmaker(bind=async_db_engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
