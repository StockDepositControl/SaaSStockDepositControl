import os
from fastapi import Depends

from backend.app.ports.security import TokenProvider, PasswordHasher
from backend.app.users.services import AuthService
from backend.adapters.repositories.user_repository import SQLAlchemyUserRepository
from backend.adapters.database.connection import get_users_session_factory
from backend.api.dependencies import get_token_provider, get_password_hasher

def get_auth_service(
    token_provider: TokenProvider = Depends(get_token_provider),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> AuthService:
    """
    FastAPI dependency that instantiates the SQLAlchemyUserRepository using the
    Users database session factory and returns the configured AuthService.
    """
    session_factory = get_users_session_factory()
    user_repo = SQLAlchemyUserRepository(session_factory)
    expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    return AuthService(
        user_repository=user_repo,
        password_hasher=password_hasher,
        token_provider=token_provider,
        access_token_expire_minutes=expire_minutes
    )
