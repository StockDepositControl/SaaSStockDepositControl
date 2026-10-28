from datetime import datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from backend.adapters.repositories.audit_repository import SQLAlchemyAuditRepository
from backend.adapters.repositories.models import AuditRecord
from backend.app.articles.models import ArticuloAdminOut, ArticuloPublicOut
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

NOW = datetime(2026, 1, 1, 10, 0, 0)


def _audit(session_id, article, user_id, scanned_at=NOW):
    return AuditRecord(
        tenant_id=1,
        session_id=session_id,
        branch_id=1,
        warehouse_id=1,
        article_code=article,
        user_id=user_id,
        action_type="NO_ACTION",
        affected_amount=0,
        audit_quantity=1,
        applied_unit_cost=Decimal("1.0000"),
        applied_vat_rate=Decimal("0.2100"),
        valorized_amount=Decimal("0"),
        scan_timestamp=scanned_at,
    )


@pytest_asyncio.fixture
async def analytics_factory(db_engines):
    return async_sessionmaker(
        bind=db_engines["analytics"], expire_on_commit=False, class_=AsyncSession
    )


@pytest.mark.asyncio
async def test_latest_audit_users_maps_article_to_user(analytics_factory):
    async with analytics_factory() as s:
        s.add(_audit(10, "ART-001", 42))
        await s.commit()

    repo = SQLAlchemyAuditRepository(analytics_factory)
    result = await repo.get_latest_audit_users_for_articles(
        session_id=10, article_ids=["ART-001"]
    )

    assert result == {"ART-001": 42}


@pytest.mark.asyncio
async def test_latest_audit_users_picks_most_recent_scan(analytics_factory):
    async with analytics_factory() as s:
        s.add_all(
            [
                _audit(10, "ART-001", 7, NOW),
                _audit(10, "ART-001", 42, NOW + timedelta(minutes=5)),
            ]
        )
        await s.commit()

    repo = SQLAlchemyAuditRepository(analytics_factory)
    result = await repo.get_latest_audit_users_for_articles(
        session_id=10, article_ids=["ART-001"]
    )

    assert result == {"ART-001": 42}


@pytest.mark.asyncio
async def test_latest_audit_users_breaks_timestamp_ties_by_latest_audit_id(
    analytics_factory,
):
    async with analytics_factory() as s:
        s.add(_audit(10, "ART-001", 42, NOW))
        await s.commit()
        s.add(_audit(10, "ART-001", 7, NOW))
        await s.commit()

    repo = SQLAlchemyAuditRepository(analytics_factory)
    result = await repo.get_latest_audit_users_for_articles(
        session_id=10, article_ids=["ART-001"]
    )

    assert result == {"ART-001": 7}


@pytest.mark.asyncio
async def test_latest_audit_users_scoped_to_session_and_requested_ids(
    analytics_factory,
):
    async with analytics_factory() as s:
        s.add_all(
            [
                _audit(10, "ART-001", 42),
                _audit(11, "ART-002", 99),
                _audit(10, "ART-003", 5),
            ]
        )
        await s.commit()

    repo = SQLAlchemyAuditRepository(analytics_factory)
    result = await repo.get_latest_audit_users_for_articles(
        session_id=10, article_ids=["ART-001", "ART-002"]
    )

    assert result == {"ART-001": 42}


@pytest.mark.asyncio
async def test_latest_audit_users_empty_ids_returns_empty(analytics_factory):
    repo = SQLAlchemyAuditRepository(analytics_factory)
    assert (
        await repo.get_latest_audit_users_for_articles(session_id=10, article_ids=[])
        == {}
    )


def test_unaudited_article_output_has_null_audited_by():
    public = ArticuloPublicOut(id_articulo="ART-002", des_articulo="X")
    admin = ArticuloAdminOut(
        id_articulo="ART-002", des_articulo="X", pcio_com_siva=Decimal("1")
    )

    assert public.model_dump(mode="json")["audited_by"] is None
    assert public.fue_auditado is False
    assert admin.model_dump(mode="json")["audited_by"] is None


def test_audited_article_output_exposes_audited_by():
    out = ArticuloPublicOut(
        id_articulo="ART-001",
        des_articulo="X",
        fue_auditado=True,
        audited_by="Carlos Auditor",
    )
    assert out.model_dump(mode="json")["audited_by"] == "Carlos Auditor"
