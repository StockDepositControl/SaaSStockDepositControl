from abc import ABC, abstractmethod
from typing import AsyncContextManager, Any

class DatabaseSession(ABC):
    """
    Abstract interface representing a database transaction session.
    Keeps the domain layer isolated from specific ORM/database client implementations.
    """
    @abstractmethod
    async def commit(self) -> None:
        """Commits the current transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rolls back the current transaction."""
        pass

    @property
    @abstractmethod
    def raw_session(self) -> Any:
        """
        Returns the underlying database session/connection object.
        This will be cast to the specific ORM session (e.g. AsyncSession)
        within the adapters, but remains 'Any' to keep the port pure.
        """
        pass

class ConnectionProvider(ABC):
    """
    Port defining the database connection provider interface.
    Manages session creation and transaction context lifecycles.
    """
    @abstractmethod
    def session(self) -> AsyncContextManager[DatabaseSession]:
        """
        Returns an asynchronous context manager that yields an active DatabaseSession.
        """
        pass

    @abstractmethod
    async def check_connectivity(self) -> bool:
        """
        Verify that the underlying database is reachable.
        Returns True if a lightweight probe succeeds, False otherwise.
        """
        pass
