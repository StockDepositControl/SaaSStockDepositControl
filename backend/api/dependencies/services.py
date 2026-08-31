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
    FastAPI dependency that instantiates article, stock, and audit repositories and returns AuditService.
    """
    from backend.app.movements.services import AuditService, StockLookupService
    from backend.adapters.repositories.stock_repository import SQLAlchemyStockRepository
    from backend.adapters.repositories.audit_repository import SQLAlchemyAuditRepository
    from backend.adapters.repositories.article_repository import SQLAlchemyArticleRepository
    from backend.adapters.repositories.work_session_repository import SQLAlchemyWorkSessionRepository
    from backend.app.work_sessions.services import WorkSessionService
    from backend.adapters.database.connection import get_analytics_session_factory

    stock_repo = SQLAlchemyStockRepository()
    audit_repo = SQLAlchemyAuditRepository()
    article_repo = SQLAlchemyArticleRepository()
    
    ws_session_factory = get_analytics_session_factory()
    ws_repo = SQLAlchemyWorkSessionRepository(ws_session_factory)
    ws_service = WorkSessionService(repository=ws_repo)

    stock_lookup_svc = StockLookupService(stock_repository=stock_repo, audit_repository=audit_repo)
    return AuditService(
        article_repository=article_repo,
        audit_repository=audit_repo,
        stock_lookup_service=stock_lookup_svc,
        work_session_service=ws_service
    )


def get_work_session_service() -> "WorkSessionService":
    """
    FastAPI dependency for WorkSessionService.
    """
    from backend.app.work_sessions.services import WorkSessionService
    from backend.adapters.repositories.work_session_repository import SQLAlchemyWorkSessionRepository
    from backend.adapters.database.connection import get_analytics_session_factory

    session_factory = get_analytics_session_factory()
    repo = SQLAlchemyWorkSessionRepository(session_factory)
    return WorkSessionService(repository=repo)


def get_enterprise_service() -> "EnterpriseService":
    """
    FastAPI dependency for EnterpriseService.
    """
    from backend.app.enterprises.services import EnterpriseService
    from backend.adapters.repositories.enterprise_repository import SQLAlchemyEnterpriseRepository

    enterprise_repo = SQLAlchemyEnterpriseRepository()
    return EnterpriseService(enterprise_repository=enterprise_repo)


def get_branch_service() -> "BranchService":
    """
    FastAPI dependency for BranchService.
    """
    from backend.app.branches.services import BranchService
    from backend.adapters.repositories.branch_repository import SQLAlchemyBranchRepository
    from backend.adapters.repositories.enterprise_repository import SQLAlchemyEnterpriseRepository

    enterprise_repo = SQLAlchemyEnterpriseRepository()
    branch_repo = SQLAlchemyBranchRepository()
    return BranchService(branch_repository=branch_repo, enterprise_repository=enterprise_repo)

