from backend.app.ports.database import ConnectionProvider
from backend.adapters.database.connection import SQLAlchemyConnectionProvider

# Singleton instance of ConnectionProvider to manage pool resources across requests
_connection_provider: ConnectionProvider | None = None

def get_connection_provider() -> ConnectionProvider:
    """
    Dependency injection provider returning the ConnectionProvider port.
    Guarantees a singleton pattern for connection pool management.
    """
    global _connection_provider
    if _connection_provider is None:
        _connection_provider = SQLAlchemyConnectionProvider()
    return _connection_provider
