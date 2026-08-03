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


def get_article_search_service() -> "ArticleSearchService":
    """
    FastAPI dependency that instantiates the SQLAlchemyArticleRepository using the
    Articles database session factory and returns the configured ArticleSearchService.
    """
    from backend.app.articles.services import ArticleSearchService
    from backend.adapters.repositories.article_repository import SQLAlchemyArticleRepository
    from backend.adapters.database.connection import get_articles_session_factory

    session_factory = get_articles_session_factory()
    repo = SQLAlchemyArticleRepository(session_factory)
    return ArticleSearchService(article_repository=repo)


def get_audit_service() -> "AuditService":
    """
    FastAPI dependency that instantiates stock and audit repositories and returns AuditService.
    """
    from backend.app.movements.services import AuditService
    from backend.adapters.repositories.stock_repository import SQLAlchemyStockRepository
    from backend.adapters.repositories.audit_repository import SQLAlchemyAuditRepository

    stock_repo = SQLAlchemyStockRepository()
    audit_repo = SQLAlchemyAuditRepository()
    return AuditService(stock_repository=stock_repo, audit_repository=audit_repo)
