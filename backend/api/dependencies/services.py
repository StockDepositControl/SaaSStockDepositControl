import os
from typing import TYPE_CHECKING

from backend.adapters.database.connection import get_users_session_factory
from backend.adapters.repositories.user_repository import SQLAlchemyUserRepository
from backend.api.dependencies import get_password_hasher, get_token_provider
from backend.app.ports.security import PasswordHasher, TokenProvider
from backend.app.users.services import AuthService
from fastapi import Depends

if TYPE_CHECKING:
    from backend.app.articles.orchestrator import ArticleCatalogOrchestrator
    from backend.app.articles.services import ArticleSearchService
    from backend.app.branches.services import BranchService
    from backend.app.enterprises.services import EnterpriseService
    from backend.app.movements.services import (
        AuditService,
        StockKPIService,
        StockLookupService,
    )
    from backend.app.reports.ports import DailyInventoryBalanceReportRepositoryPort
    from backend.app.reports.services import (
        DailyInventoryBalanceReportService,
        GoodsReceivedReportService,
        ShrinkageReportService,
    )
    from backend.app.users.services import UserService
    from backend.app.work_sessions.services import WorkSessionService


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
        access_token_expire_minutes=expire_minutes,
    )


def get_user_service() -> "UserService":
    """
    FastAPI dependency that instantiates the SQLAlchemyUserRepository using the
    Users database session factory and returns the configured UserService.
    """
    from backend.app.users.services import UserService

    session_factory = get_users_session_factory()
    user_repo = SQLAlchemyUserRepository(session_factory)
    return UserService(user_repository=user_repo)


def get_article_search_service() -> "ArticleSearchService":
    """
    FastAPI dependency that instantiates the SQLAlchemyArticleRepository using the
    Articles database session factory and returns the configured ArticleSearchService.
    """
    from backend.adapters.database.connection import get_articles_session_factory
    from backend.adapters.repositories.article_repository import (
        SQLAlchemyArticleRepository,
    )
    from backend.app.articles.services import ArticleSearchService

    session_factory = get_articles_session_factory()
    repo = SQLAlchemyArticleRepository(session_factory)
    return ArticleSearchService(article_repository=repo)


def get_stock_lookup_service() -> "StockLookupService":
    """
    FastAPI dependency that instantiates and returns StockLookupService.
    """
    from backend.adapters.repositories.audit_repository import SQLAlchemyAuditRepository
    from backend.adapters.repositories.stock_repository import SQLAlchemyStockRepository
    from backend.app.movements.services import StockLookupService

    stock_repo = SQLAlchemyStockRepository()
    audit_repo = SQLAlchemyAuditRepository()
    return StockLookupService(stock_repository=stock_repo, audit_repository=audit_repo)


def get_article_catalog_orchestrator(
    search_service: "ArticleSearchService" = Depends(get_article_search_service),
    stock_lookup_service: "StockLookupService" = Depends(get_stock_lookup_service),
) -> "ArticleCatalogOrchestrator":
    """
    FastAPI dependency that instantiates and returns the ArticleCatalogOrchestrator,
    wired with the db_users repository for auditor-name resolution.
    """
    from backend.adapters.database.connection import get_users_session_factory
    from backend.adapters.repositories.user_repository import SQLAlchemyUserRepository
    from backend.app.articles.orchestrator import ArticleCatalogOrchestrator

    return ArticleCatalogOrchestrator(
        article_search_service=search_service,
        stock_lookup_service=stock_lookup_service,
        user_repository=SQLAlchemyUserRepository(get_users_session_factory()),
    )


def get_audit_service() -> "AuditService":
    """
    FastAPI dependency that instantiates article, stock, and audit repositories and
    returns AuditService.
    """
    from backend.adapters.database.connection import get_analytics_session_factory
    from backend.adapters.repositories.article_repository import (
        SQLAlchemyArticleRepository,
    )
    from backend.adapters.repositories.audit_repository import SQLAlchemyAuditRepository
    from backend.adapters.repositories.stock_repository import SQLAlchemyStockRepository
    from backend.adapters.repositories.work_session_repository import (
        SQLAlchemyWorkSessionRepository,
    )
    from backend.app.movements.services import AuditService, StockLookupService
    from backend.app.work_sessions.services import WorkSessionService

    stock_repo = SQLAlchemyStockRepository()
    audit_repo = SQLAlchemyAuditRepository()
    article_repo = SQLAlchemyArticleRepository()

    ws_session_factory = get_analytics_session_factory()
    ws_repo = SQLAlchemyWorkSessionRepository(ws_session_factory)
    ws_service = WorkSessionService(repository=ws_repo)

    stock_lookup_svc = StockLookupService(
        stock_repository=stock_repo, audit_repository=audit_repo
    )
    return AuditService(
        article_repository=article_repo,
        audit_repository=audit_repo,
        stock_lookup_service=stock_lookup_svc,
        work_session_service=ws_service,
    )


def get_stock_kpi_service() -> "StockKPIService":
    """
    FastAPI dependency for the read-only StockKPIService.
    """
    from backend.adapters.repositories.audit_repository import SQLAlchemyAuditRepository
    from backend.adapters.repositories.stock_repository import SQLAlchemyStockRepository
    from backend.app.movements.services import StockKPIService

    return StockKPIService(
        stock_repository=SQLAlchemyStockRepository(),
        audit_repository=SQLAlchemyAuditRepository(),
    )


def get_work_session_service() -> "WorkSessionService":
    """
    FastAPI dependency for WorkSessionService.
    """
    from backend.adapters.database.connection import get_analytics_session_factory
    from backend.adapters.repositories.work_session_repository import (
        SQLAlchemyWorkSessionRepository,
    )
    from backend.app.work_sessions.services import WorkSessionService

    session_factory = get_analytics_session_factory()
    repo = SQLAlchemyWorkSessionRepository(session_factory)
    return WorkSessionService(repository=repo)


def get_enterprise_service() -> "EnterpriseService":
    """
    FastAPI dependency for EnterpriseService.
    """
    from backend.adapters.repositories.enterprise_repository import (
        SQLAlchemyEnterpriseRepository,
    )
    from backend.app.enterprises.services import EnterpriseService

    enterprise_repo = SQLAlchemyEnterpriseRepository()
    return EnterpriseService(enterprise_repository=enterprise_repo)


def get_branch_service() -> "BranchService":
    """
    FastAPI dependency for BranchService.
    """
    from backend.adapters.repositories.branch_repository import (
        SQLAlchemyBranchRepository,
    )
    from backend.adapters.repositories.enterprise_repository import (
        SQLAlchemyEnterpriseRepository,
    )
    from backend.app.branches.services import BranchService

    enterprise_repo = SQLAlchemyEnterpriseRepository()
    branch_repo = SQLAlchemyBranchRepository()
    return BranchService(
        branch_repository=branch_repo, enterprise_repository=enterprise_repo
    )


def get_shrinkage_report_service() -> "ShrinkageReportService":
    """
    FastAPI dependency for ShrinkageReportService.
    Wires SQLAlchemyShrinkageReportRepository (db_analytics) and
    SQLAlchemyArticleRepository (db_articles).
    """
    from backend.adapters.repositories.article_repository import (
        SQLAlchemyArticleRepository,
    )
    from backend.adapters.repositories.report_repository import (
        SQLAlchemyShrinkageReportRepository,
    )
    from backend.app.reports.services import ShrinkageReportService

    report_repo = SQLAlchemyShrinkageReportRepository()
    article_repo = SQLAlchemyArticleRepository()
    return ShrinkageReportService(
        report_repository=report_repo, article_repository=article_repo
    )


def get_goods_received_report_service() -> "GoodsReceivedReportService":
    """
    FastAPI dependency for GoodsReceivedReportService.
    Wires SQLAlchemyGoodsReceivedReportRepository (db_analytics) and
    SQLAlchemyArticleRepository (db_articles).
    """
    from backend.adapters.repositories.article_repository import (
        SQLAlchemyArticleRepository,
    )
    from backend.adapters.repositories.report_repository import (
        SQLAlchemyGoodsReceivedReportRepository,
    )
    from backend.app.reports.services import GoodsReceivedReportService

    report_repo = SQLAlchemyGoodsReceivedReportRepository()
    article_repo = SQLAlchemyArticleRepository()
    return GoodsReceivedReportService(
        report_repository=report_repo, article_repository=article_repo
    )


def get_daily_inventory_balance_repository() -> (
    "DailyInventoryBalanceReportRepositoryPort"
):
    """
    FastAPI dependency for DailyInventoryBalanceReportRepositoryPort.
    """
    from backend.adapters.repositories.report_repository import (
        SQLAlchemyDailyInventoryBalanceReportRepository,
    )

    return SQLAlchemyDailyInventoryBalanceReportRepository()


def get_daily_inventory_balance_report_service(
    repo=Depends(get_daily_inventory_balance_repository),
) -> "DailyInventoryBalanceReportService":
    """
    FastAPI dependency for DailyInventoryBalanceReportService.
    Wires DailyInventoryBalanceReportRepositoryPort (db_analytics).
    """
    from backend.app.reports.services import DailyInventoryBalanceReportService

    return DailyInventoryBalanceReportService(report_repository=repo)
