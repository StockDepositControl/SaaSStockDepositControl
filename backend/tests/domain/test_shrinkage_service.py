from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
import pytest

from backend.app.articles.models import Articulo
from backend.app.reports.domain import ShrinkageRawRecord, VatCalculator
from backend.app.reports.ports import ShrinkageReportRepositoryPort
from backend.app.reports.schemas import ShrinkageReportFilters
from backend.app.reports.services import ShrinkageReportService


# ============================================================================
# VatCalculator Unit Tests (Pure Fabrication)
# ============================================================================

def test_vat_calculator_unit_cost_zero_vat():
    cost = Decimal("100.00")
    vat = Decimal("0.00")
    total = VatCalculator.calculate_total_unit_cost(cost, vat)
    assert total == Decimal("100.00")
    assert isinstance(total, Decimal)


def test_vat_calculator_unit_cost_standard_vat():
    cost = Decimal("100.00")
    vat = Decimal("0.21")
    total = VatCalculator.calculate_total_unit_cost(cost, vat)
    assert total == Decimal("121.00")
    assert isinstance(total, Decimal)


def test_vat_calculator_unit_cost_custom_vat():
    cost = Decimal("200.00")
    vat = Decimal("0.105")
    total = VatCalculator.calculate_total_unit_cost(cost, vat)
    assert total == Decimal("221.00")
    assert isinstance(total, Decimal)


def test_vat_calculator_financial_loss():
    quantity = 7
    unit_cost = Decimal("121.00")
    loss = VatCalculator.calculate_financial_loss(quantity, unit_cost)
    assert loss == Decimal("847.00")
    assert isinstance(loss, Decimal)


# ============================================================================
# ShrinkageReportService Unit Tests (Mocked Ports)
# ============================================================================

@pytest.fixture
def mock_report_repo():
    return AsyncMock(spec=ShrinkageReportRepositoryPort)


@pytest.fixture
def mock_article_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def report_service(mock_report_repo, mock_article_repo):
    return ShrinkageReportService(
        report_repository=mock_report_repo,
        article_repository=mock_article_repo,
    )


@pytest.mark.asyncio
async def test_get_shrinkage_report_empty(report_service, mock_report_repo):
    mock_report_repo.fetch_shrinkage_records.return_value = []

    filters = ShrinkageReportFilters(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    result = await report_service.get_shrinkage_report(tenant_id="1", filters=filters)

    assert result.total_items == 0
    assert result.total_shrinkage_units == 0
    assert result.total_financial_erosion == Decimal("0.00")
    assert len(result.line_items) == 0


@pytest.mark.asyncio
async def test_get_shrinkage_report_with_medication_and_standard_vat(
    report_service, mock_report_repo, mock_article_repo
):
    now = datetime(2026, 1, 15, 10, 0, 0)
    mock_report_repo.fetch_shrinkage_records.return_value = [
        ShrinkageRawRecord(
            audit_id=1,
            article_code="MED01",
            affected_amount=4,
            applied_unit_cost=Decimal("50.00"),
            applied_vat_rate=Decimal("0.00"),
            valorized_amount=Decimal("200.00"),
            scan_timestamp=now,
            branch_id=1,
        ),
        ShrinkageRawRecord(
            audit_id=2,
            article_code="PERF01",
            affected_amount=3,
            applied_unit_cost=Decimal("100.00"),
            applied_vat_rate=Decimal("0.21"),
            valorized_amount=Decimal("363.00"),
            scan_timestamp=now,
            branch_id=1,
        ),
    ]

    async def get_article_side_effect(article_code, *args, **kwargs):
        if article_code == "MED01":
            return Articulo(
                id_articulo="MED01",
                des_articulo="Ibuprofeno 400mg",
                des_familia="Medicamentos",
                pcio_com_siva=Decimal("50.00"),
            )
        elif article_code == "PERF01":
            return Articulo(
                id_articulo="PERF01",
                des_articulo="Shampoo Anticaspa",
                des_familia="Perfumeria",
                pcio_com_siva=Decimal("100.00"),
            )
        return None

    mock_article_repo.get_by_id.side_effect = get_article_side_effect

    filters = ShrinkageReportFilters(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        default_vat_rate=Decimal("0.21"),
    )

    result = await report_service.get_shrinkage_report(tenant_id="1", filters=filters)

    assert result.total_items == 2
    assert result.total_shrinkage_units == 7

    med_item = next(i for i in result.line_items if i.article_code == "MED01")
    assert med_item.vat_rate == Decimal("0.00")
    assert med_item.total_unit_cost == Decimal("50.00")
    assert med_item.total_quantity == 4
    assert med_item.total_financial_loss == Decimal("200.00")

    perf_item = next(i for i in result.line_items if i.article_code == "PERF01")
    assert perf_item.vat_rate == Decimal("0.21")
    assert perf_item.total_unit_cost == Decimal("121.00")
    assert perf_item.total_quantity == 3
    assert perf_item.total_financial_loss == Decimal("363.00")

    # Grand total financial erosion = 200 + 363 = 563.00
    assert result.total_financial_erosion == Decimal("563.00")
    assert isinstance(result.total_financial_erosion, Decimal)


@pytest.mark.asyncio
async def test_get_shrinkage_report_consolidates_multiple_records_same_article(
    report_service, mock_report_repo, mock_article_repo
):
    now = datetime(2026, 2, 10, 12, 0, 0)
    mock_report_repo.fetch_shrinkage_records.return_value = [
        ShrinkageRawRecord(
            audit_id=10,
            article_code="ITEM_A",
            affected_amount=3,
            applied_unit_cost=Decimal("20.00"),
            applied_vat_rate=Decimal("0.21"),
            valorized_amount=Decimal("72.60"),
            scan_timestamp=now,
            branch_id=1,
        ),
        ShrinkageRawRecord(
            audit_id=11,
            article_code="ITEM_A",
            affected_amount=7,
            applied_unit_cost=Decimal("20.00"),
            applied_vat_rate=Decimal("0.21"),
            valorized_amount=Decimal("169.40"),
            scan_timestamp=now,
            branch_id=2,
        ),
    ]

    mock_article_repo.get_by_id.return_value = Articulo(
        id_articulo="ITEM_A",
        des_articulo="Gasa Esteril",
        des_familia="Material Descartable",
        pcio_com_siva=Decimal("20.00"),
    )

    filters = ShrinkageReportFilters(
        start_date=date(2026, 2, 1),
        end_date=date(2026, 2, 28),
    )

    result = await report_service.get_shrinkage_report(tenant_id="1", filters=filters)

    assert result.total_items == 1
    assert result.total_shrinkage_units == 10
    item = result.line_items[0]
    assert item.total_quantity == 10
    assert item.total_unit_cost == Decimal("24.20")
    assert item.total_financial_loss == Decimal("242.00")
    assert result.total_financial_erosion == Decimal("242.00")


@pytest.mark.asyncio
async def test_get_shrinkage_report_article_not_found_graceful(
    report_service, mock_report_repo, mock_article_repo
):
    now = datetime(2026, 1, 1, 10, 0, 0)
    mock_report_repo.fetch_shrinkage_records.return_value = [
        ShrinkageRawRecord(
            audit_id=99,
            article_code="NONEXISTENT",
            affected_amount=5,
            applied_unit_cost=Decimal("10.00"),
            applied_vat_rate=Decimal("0.21"),
            valorized_amount=Decimal("60.50"),
            scan_timestamp=now,
            branch_id=1,
        )
    ]
    mock_article_repo.get_by_id.return_value = None

    filters = ShrinkageReportFilters(
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    result = await report_service.get_shrinkage_report(tenant_id="1", filters=filters)

    assert result.total_items == 1
    item = result.line_items[0]
    assert item.des_articulo == "Artículo desconocido"
    assert item.total_quantity == 5
    assert item.total_financial_loss == Decimal("0.00")
