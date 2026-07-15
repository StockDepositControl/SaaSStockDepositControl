import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

from backend.app.ports.database import ConnectionProvider, DatabaseSession
from backend.adapters.database.connection import SQLAlchemyConnectionProvider, SQLAlchemyDatabaseSession

# --- Domain Layer Isolation Test ---

class DummyRepository:
    """A dummy domain repository that accepts the database session."""
    def __init__(self, session: DatabaseSession):
        self.session = session

    async def get_data(self) -> str:
        return "data"

class DummyDomainService:
    """A pure domain service that manages transactions via ConnectionProvider."""
    def __init__(self, connection_provider: ConnectionProvider):
        self.connection_provider = connection_provider

    async def perform_action(self) -> str:
        async with self.connection_provider.session() as session:
            repo = DummyRepository(session)
            data = await repo.get_data()
            await session.commit()
            return data

class MockDatabaseSession(DatabaseSession):
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    @property
    def raw_session(self) -> str:
        return "mocked_underlying_connection"

class MockConnectionProvider(ConnectionProvider):
    def __init__(self, mock_session: MockDatabaseSession):
        self.mock_session = mock_session

    @asynccontextmanager
    async def session(self):
        yield self.mock_session

@pytest.mark.asyncio
async def test_domain_layer_isolation():
    # Arrange
    mock_session = MockDatabaseSession()
    mock_provider = MockConnectionProvider(mock_session)
    service = DummyDomainService(mock_provider)

    # Act
    result = await service.perform_action()

    # Assert
    assert result == "data"
    assert mock_session.committed is True
    assert mock_session.rolled_back is False


# --- Adapter Unit Test (Mocked SQLAlchemy) ---

@pytest.mark.asyncio
@patch('backend.adapters.database.connection.create_async_engine')
@patch('backend.adapters.database.connection.async_sessionmaker')
async def test_sqlalchemy_adapter_lifecycle(mock_sessionmaker, mock_create_engine):
    # Arrange
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    class MockContextManager:
        async def __aenter__(self):
            return mock_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_sessionmaker.return_value = MagicMock(return_value=MockContextManager())

    # Create adapter with fake database URL (mocked engine prevents connection attempt)
    provider = SQLAlchemyConnectionProvider(database_url="mysql+aiomysql://mock:mock@mock/mock")
    provider.session_factory = mock_sessionmaker()

    # Act
    async with provider.session() as session:
        assert isinstance(session, SQLAlchemyDatabaseSession)
        assert session.raw_session == mock_session
        await session.commit()

    # Assert
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


@pytest.mark.asyncio
@patch('backend.adapters.database.connection.create_async_engine')
@patch('backend.adapters.database.connection.async_sessionmaker')
async def test_sqlalchemy_adapter_rollback_on_exception(mock_sessionmaker, mock_create_engine):
    # Arrange
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    class MockContextManager:
        async def __aenter__(self):
            return mock_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_sessionmaker.return_value = MagicMock(return_value=MockContextManager())

    provider = SQLAlchemyConnectionProvider(database_url="mysql+aiomysql://mock:mock@mock/mock")
    provider.session_factory = mock_sessionmaker()

    # Act & Assert
    with pytest.raises(ValueError, match="Database error"):
        async with provider.session() as session:
            assert session.raw_session == mock_session
            raise ValueError("Database error")

    # Assert
    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()
    mock_session.commit.assert_not_called()
