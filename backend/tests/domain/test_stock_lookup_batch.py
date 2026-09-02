import pytest
from unittest.mock import AsyncMock

from backend.app.movements.ports import StockRepositoryPort, AuditRepositoryPort
from backend.app.movements.services import StockLookupService


@pytest.fixture
def mock_stock_repo():
    return AsyncMock(spec=StockRepositoryPort)


@pytest.fixture
def mock_audit_repo():
    return AsyncMock(spec=AuditRepositoryPort)


@pytest.fixture
def stock_lookup_service(mock_stock_repo, mock_audit_repo):
    return StockLookupService(
        stock_repository=mock_stock_repo,
        audit_repository=mock_audit_repo,
    )


@pytest.mark.asyncio
async def test_get_effective_stocks_batch_empty(stock_lookup_service, mock_stock_repo, mock_audit_repo):
    result = await stock_lookup_service.get_effective_stocks_batch(
        article_ids=[],
        deposit_id=1,
        active_session_id=10,
    )
    assert result == {}
    mock_audit_repo.get_latest_audits_for_articles.assert_not_called()
    mock_stock_repo.get_stock_positions_batch.assert_not_called()


@pytest.mark.asyncio
async def test_get_effective_stocks_batch_audit_overrides_stock(stock_lookup_service, mock_stock_repo, mock_audit_repo):
    # Article "A1" has an audit record (audit_qty = 50)
    # Article "A2" has no audit record, but has stock in DB (stock = 25)
    mock_audit_repo.get_latest_audits_for_articles.return_value = {"A1": 50}
    mock_stock_repo.get_stock_positions_batch.return_value = {"A2": 25}

    result = await stock_lookup_service.get_effective_stocks_batch(
        article_ids=["A1", "A2"],
        deposit_id=1,
        active_session_id=10,
    )

    assert result == {"A1": 50, "A2": 25}
    mock_audit_repo.get_latest_audits_for_articles.assert_called_once_with(
        session_id=10,
        article_ids=["A1", "A2"],
    )
    # Only remaining IDs (A2) should be queried in stock_repo
    mock_stock_repo.get_stock_positions_batch.assert_called_once_with(
        deposit_id=1,
        article_ids=["A2"],
    )


@pytest.mark.asyncio
async def test_get_effective_stocks_batch_all_audited(stock_lookup_service, mock_stock_repo, mock_audit_repo):
    mock_audit_repo.get_latest_audits_for_articles.return_value = {"A1": 10, "A2": 20}

    result = await stock_lookup_service.get_effective_stocks_batch(
        article_ids=["A1", "A2"],
        deposit_id=1,
        active_session_id=10,
    )

    assert result == {"A1": 10, "A2": 20}
    mock_stock_repo.get_stock_positions_batch.assert_not_called()


@pytest.mark.asyncio
async def test_get_effective_stocks_batch_no_session(stock_lookup_service, mock_stock_repo, mock_audit_repo):
    mock_stock_repo.get_stock_positions_batch.return_value = {"A1": 100, "A2": 200}

    result = await stock_lookup_service.get_effective_stocks_batch(
        article_ids=["A1", "A2"],
        deposit_id=1,
        active_session_id=None,
    )

    assert result == {"A1": 100, "A2": 200}
    mock_audit_repo.get_latest_audits_for_articles.assert_not_called()
    mock_stock_repo.get_stock_positions_batch.assert_called_once_with(
        deposit_id=1,
        article_ids=["A1", "A2"],
    )
