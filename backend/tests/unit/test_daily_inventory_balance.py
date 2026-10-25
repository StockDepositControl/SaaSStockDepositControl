from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from backend.adapters.repositories.models.analytics import AuditRecord as AuditRecordORM
from backend.adapters.repositories.report_repository import (
    SQLAlchemyDailyInventoryBalanceReportRepository,
)
from backend.app.reports.domain import DailyInventoryBalanceRecord
from backend.app.reports.ports import DailyInventoryBalanceReportRepositoryPort
from backend.app.reports.schemas import (
    DailyInventoryBalanceFilters,
    DailyInventoryBalanceResponse,
)
from backend.app.reports.services import DailyInventoryBalanceReportService


@pytest.fixture
def mock_report_repo():
    return AsyncMock(spec=DailyInventoryBalanceReportRepositoryPort)


@pytest.fixture
def balance_service(mock_report_repo):
    return DailyInventoryBalanceReportService(report_repository=mock_report_repo)


@pytest.mark.asyncio
async def test_daily_balance_service_empty_records(balance_service, mock_report_repo):
    mock_report_repo.fetch_daily_balance_records.return_value = []

    filters = DailyInventoryBalanceFilters(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    result = await balance_service.get_daily_inventory_balance_report(
        tenant_id="1", filters=filters
    )

    assert isinstance(result, DailyInventoryBalanceResponse)
    assert result.tenant_id == "1"
    assert result.branch_id is None
    assert result.total_days == 0
    assert result.total_addition_value == Decimal("0.00")
    assert result.total_shrinkage_value == Decimal("0.00")
    assert result.net_patrimonial_variation == Decimal("0.00")
    assert len(result.daily_summaries) == 0


@pytest.mark.asyncio
async def test_daily_balance_service_net_patrimonial_math(
    balance_service, mock_report_repo
):
    record = DailyInventoryBalanceRecord(
        tenant_id=1,
        branch_id=1,
        report_date=date(2026, 1, 15),
        total_audit_articles=50,
        total_processed_units=1200,
        total_addition_amount=800,
        total_shrinkage_amount=150,
        total_addition_value=Decimal("250000.00"),
        total_shrinkage_value=Decimal("45000.00"),
        net_patrimonial_variation=Decimal("205000.00"),
    )
    mock_report_repo.fetch_daily_balance_records.return_value = [record]

    filters = DailyInventoryBalanceFilters(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    result = await balance_service.get_daily_inventory_balance_report(
        tenant_id="1", filters=filters
    )

    assert result.total_days == 1
    assert result.total_addition_value == Decimal("250000.00")
    assert result.total_shrinkage_value == Decimal("45000.00")
    assert result.net_patrimonial_variation == Decimal("205000.00")
    assert isinstance(result.net_patrimonial_variation, Decimal)

    summary = result.daily_summaries[0]
    assert summary.report_date == date(2026, 1, 15)
    assert summary.total_audit_articles == 50
    assert summary.total_processed_units == 1200
    assert summary.total_addition_units == 800
    assert summary.total_shrinkage_units == 150
    assert summary.total_addition_value == Decimal("250000.00")
    assert summary.total_shrinkage_value == Decimal("45000.00")
    assert summary.net_patrimonial_variation == Decimal("205000.00")


@pytest.mark.asyncio
async def test_daily_balance_service_multi_day_aggregation(
    balance_service, mock_report_repo
):
    records = [
        DailyInventoryBalanceRecord(
            tenant_id=1,
            branch_id=1,
            report_date=date(2026, 2, 1),
            total_audit_articles=20,
            total_processed_units=500,
            total_addition_amount=300,
            total_shrinkage_amount=50,
            total_addition_value=Decimal("1000.00"),
            total_shrinkage_value=Decimal("200.00"),
            net_patrimonial_variation=Decimal("800.00"),
        ),
        DailyInventoryBalanceRecord(
            tenant_id=1,
            branch_id=1,
            report_date=date(2026, 2, 2),
            total_audit_articles=30,
            total_processed_units=600,
            total_addition_amount=100,
            total_shrinkage_amount=250,
            total_addition_value=Decimal("500.00"),
            total_shrinkage_value=Decimal("800.00"),
            net_patrimonial_variation=Decimal("-300.00"),
        ),
    ]
    mock_report_repo.fetch_daily_balance_records.return_value = records

    filters = DailyInventoryBalanceFilters(
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 28),
    )

    result = await balance_service.get_daily_inventory_balance_report(
        tenant_id="1", filters=filters
    )

    assert result.total_days == 2
    assert result.total_addition_value == Decimal("1500.00")
    assert result.total_shrinkage_value == Decimal("1000.00")
    assert result.net_patrimonial_variation == Decimal("500.00")
    assert len(result.daily_summaries) == 2
    assert result.daily_summaries[0].net_patrimonial_variation == Decimal("800.00")
    assert result.daily_summaries[1].net_patrimonial_variation == Decimal("-300.00")


@pytest.mark.asyncio
async def test_daily_balance_service_branch_filter_passthrough(
    balance_service, mock_report_repo
):
    mock_report_repo.fetch_daily_balance_records.return_value = []

    filters = DailyInventoryBalanceFilters(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 10),
        branch_id=3,
    )

    result = await balance_service.get_daily_inventory_balance_report(
        tenant_id="1", filters=filters
    )

    assert result.branch_id == 3
    mock_report_repo.fetch_daily_balance_records.assert_awaited_once_with(
        tenant_id=1,
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 10),
        branch_id=3,
    )


@pytest.mark.asyncio
async def test_daily_balance_service_non_numeric_tenant_id_fallback(
    balance_service, mock_report_repo
):
    mock_report_repo.fetch_daily_balance_records.return_value = []

    filters = DailyInventoryBalanceFilters(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    result = await balance_service.get_daily_inventory_balance_report(
        tenant_id="tenant-xyz", filters=filters
    )

    assert result.tenant_id == "tenant-xyz"
    mock_report_repo.fetch_daily_balance_records.assert_awaited_once_with(
        tenant_id=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        branch_id=None,
    )


@pytest.mark.asyncio
async def test_repository_fallback_aggregation_from_audit_records():
    # Test fallback aggregation directly on the repository adapter
    mock_session = AsyncMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    # First query to DailyReport returns empty
    mock_daily_report_result = MagicMock()
    mock_daily_report_result.scalars.return_value.all.return_value = []

    # Second query to AuditRecord returns raw audit rows
    dt1 = datetime(2026, 1, 10, 10, 0, 0)
    dt2 = datetime(2026, 1, 10, 14, 0, 0)
    mock_audit_row_1 = MagicMock(spec=AuditRecordORM)
    mock_audit_row_1.tenant_id = 1
    mock_audit_row_1.branch_id = 2
    mock_audit_row_1.article_code = "ART01"
    mock_audit_row_1.scan_timestamp = dt1
    mock_audit_row_1.action_type = "ADDITION"
    mock_audit_row_1.affected_amount = 10
    mock_audit_row_1.valorized_amount = Decimal("1500.00")

    mock_audit_row_2 = MagicMock(spec=AuditRecordORM)
    mock_audit_row_2.tenant_id = 1
    mock_audit_row_2.branch_id = 2
    mock_audit_row_2.article_code = "ART02"
    mock_audit_row_2.scan_timestamp = dt2
    mock_audit_row_2.action_type = "REMOVAL"
    mock_audit_row_2.affected_amount = 4
    mock_audit_row_2.valorized_amount = Decimal("300.00")

    mock_audit_result = MagicMock()
    mock_audit_result.scalars.return_value.all.return_value = [
        mock_audit_row_1,
        mock_audit_row_2,
    ]

    mock_session.execute.side_effect = [
        mock_daily_report_result,
        mock_audit_result,
    ]

    repo = SQLAlchemyDailyInventoryBalanceReportRepository(
        session_factory=mock_session_factory
    )
    records = await repo.fetch_daily_balance_records(
        tenant_id=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        branch_id=2,
    )

    assert len(records) == 1
    rec = records[0]
    assert rec.tenant_id == 1
    assert rec.branch_id == 2
    assert rec.report_date == date(2026, 1, 10)
    assert rec.total_audit_articles == 2
    assert rec.total_processed_units == 14
    assert rec.total_addition_amount == 10
    assert rec.total_shrinkage_amount == 4
    assert rec.total_addition_value == Decimal("1500.00")
    assert rec.total_shrinkage_value == Decimal("300.00")
    assert rec.net_patrimonial_variation == Decimal("1200.00")
