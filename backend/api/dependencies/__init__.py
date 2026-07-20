import os
from backend.app.ports.database import ConnectionProvider
from backend.adapters.database.connection import SQLAlchemyConnectionProvider
from backend.app.ports.security import TokenProvider, PasswordHasher
from backend.adapters.security.jwt_provider import PyJWTTokenProvider
from backend.adapters.security.password_hasher import BcryptPasswordHasher

# Singleton instances
_connection_provider: ConnectionProvider | None = None
_token_provider: TokenProvider | None = None
_password_hasher: PasswordHasher | None = None

def get_connection_provider() -> ConnectionProvider:
    """
    Dependency injection provider returning the ConnectionProvider port.
    Guarantees a singleton pattern for connection pool management.
    """
    global _connection_provider
    if _connection_provider is None:
        _connection_provider = SQLAlchemyConnectionProvider()
    return _connection_provider

def get_token_provider() -> TokenProvider:
    """
    Dependency injection provider returning the TokenProvider port.
    Guarantees a singleton pattern for JWT token management.
    """
    global _token_provider
    if _token_provider is None:
        secret_key = os.getenv("SECRET_KEY", "supersecret-dev-key")
        _token_provider = PyJWTTokenProvider(secret_key=secret_key)
    return _token_provider

def get_password_hasher() -> PasswordHasher:
    """
    Dependency injection provider returning the PasswordHasher port.
    Guarantees a singleton pattern for password hashing.
    """
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = BcryptPasswordHasher()
    return _password_hasher
