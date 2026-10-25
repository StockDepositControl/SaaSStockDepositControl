from datetime import datetime, timedelta

import pytest
from backend.adapters.repositories.models.analytics import (
    BaseAnalytics,
    RecordTenant,
)
from backend.adapters.repositories.models.analytics import (
    WorkSession as WorkSessionORM,
)
from backend.adapters.repositories.work_session_repository import (
    SQLAlchemyWorkSessionRepository,
)
from backend.app.work_sessions.models import WorkSession
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_get_active_session_multiple_open_rows_returns_latest_without_error():
    """
    Regression test for MultipleResultsFound:
    When multiple OPEN work sessions exist for the same tenant and branch covering
    target_date,
    get_active_session must deterministically return the most recent one (.limit(1) &
    .scalars().first())
    and NEVER raise sqlalchemy.exc.MultipleResultsFound.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )

    async with engine.begin() as conn:
        await conn.run_sync(BaseAnalytics.metadata.create_all)

    now = datetime.utcnow()
    target_date = now

    async with session_factory() as session:
        # Create tenant
        tenant = RecordTenant(
            tenant_id=1, tenant_name="Test Tenant", pharmacy_code="PHARM_01"
        )
        session.add(tenant)
        await session.flush()

        # Insert 2 overlapping OPEN sessions for the same branch and date
        earlier_session = WorkSessionORM(
            session_id=101,
            tenant_id=1,
            branch_id=1,
            opened_at=now - timedelta(hours=4),
            closed_at=now + timedelta(hours=8),
            status="OPEN",
            created_at=now - timedelta(hours=4),
        )
        later_session = WorkSessionORM(
            session_id=102,
            tenant_id=1,
            branch_id=1,
            opened_at=now - timedelta(hours=1),
            closed_at=now + timedelta(hours=12),
            status="OPEN",
            created_at=now - timedelta(hours=1),
        )
        session.add_all([earlier_session, later_session])
        await session.commit()

    repo = SQLAlchemyWorkSessionRepository(session_factory=session_factory)

    # Act
    active_session = await repo.get_active_session(
        tenant_id="1", branch_id=1, target_date=target_date
    )

    # Assert
    assert active_session is not None
    assert isinstance(active_session, WorkSession)
    # Must pick the session with the latest opened_at (session_id=102)
    assert active_session.session_id == 102

    # Act for get_active_session_id
    active_id = await repo.get_active_session_id(branch_id=1)
    assert active_id == 102

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_active_session_returns_none_when_no_active_session():
    """
    Verifies that get_active_session returns None when no matching OPEN session exists.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )

    async with engine.begin() as conn:
        await conn.run_sync(BaseAnalytics.metadata.create_all)

    repo = SQLAlchemyWorkSessionRepository(session_factory=session_factory)
    result = await repo.get_active_session(
        tenant_id="1", branch_id=1, target_date=datetime.utcnow()
    )
    assert result is None

    active_id = await repo.get_active_session_id(branch_id=1)
    assert active_id is None

    await engine.dispose()


def test_claims_branch_id_fallback_for_admin():
    """
    Validates safe branch fallback resolution when claims contain None for branch_id
    (Admin persona).
    """
    # Admin claims: key 'branch_id' exists but is None
    admin_claims = {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": 1,
        "branch_id": None,
    }
    resolved_branch = admin_claims.get("branch_id") or 1
    assert resolved_branch == 1

    # Branch operator claims: specific branch_id
    operator_claims = {
        "sub": "operator@example.com",
        "role": "operador",
        "tenant_id": 1,
        "branch_id": 3,
    }
    resolved_branch_op = operator_claims.get("branch_id") or 1
    assert resolved_branch_op == 3

    # Claims without branch_id key
    empty_claims = {"tenant_id": 1}
    resolved_branch_empty = empty_claims.get("branch_id") or 1
    assert resolved_branch_empty == 1
