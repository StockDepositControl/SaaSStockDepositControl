from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.api.dependencies.auth import get_current_user_claims
from backend.api.dependencies.services import get_goods_received_report_service
from backend.api.main import app
from backend.app.articles.models import Articulo
from backend.app.articles.ports import ArticleRepositoryPort
from backend.app.reports.domain import GoodsReceivedRawRecord, VatCalculator
from backend.app.reports.ports import GoodsReceivedReportRepositoryPort
from backend.app.reports.schemas import (
    GoodsReceivedLineItem,
    GoodsReceivedReportFilters,
    GoodsReceivedReportResponse,
)
from backend.app.reports.services import GoodsReceivedReportService


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


def test_vat_calculator_capital_injected():
    quantity = 10
    unit_cost = Decimal("121.00")
    capital = VatCalculator.calculate_financial_loss(quantity, unit_cost)
    assert capital == Decimal("1210.00")
    assert isinstance(capital, Decimal)


# ============================================================================
# GoodsReceivedReportService Unit Tests (Mocked Ports)
# ============================================================================

@pytest.fixture
def mock_report_repo():
    return AsyncMock(spec=GoodsReceivedReportRepositoryPort)


@pytest.fixture
def mock_article_repo():
    return AsyncMock(spec=ArticleRepositoryPort)


@pytest.fixture
def report_service(mock_report_repo, mock_article_repo):
    return GoodsReceivedReportService(
        report_repository=mock_report_repo,
        article_repository=mock_article_repo,
    )


@pytest.mark.asyncio
async def test_get_goods_received_report_empty(report_service, mock_report_repo):
    mock_report_repo.fetch_goods_received_records.return_value = []

    filters = GoodsReceivedReportFilters(
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )

    result = await report_service.get_goods_received_report(tenant_id="1", filters=filters)

    assert result.total_items == 0
    assert result.total_added_units == 0
    assert result.total_capital_inyectado == Decimal("0.00")
    assert len(result.line_items) == 0


@pytest.mark.asyncio
async def test_get_goods_received_report_with_medication_and_standard_vat(
    report_service, mock_report_repo, mock_article_repo
):
    now = datetime(2026, 9, 15, 10, 0, 0)
    mock_report_repo.fetch_goods_received_records.return_value = [
        GoodsReceivedRawRecord(
            audit_id=1,
            article_code="MED01",
            affected_amount=5,
            applied_unit_cost=Decimal("50.00"),
            applied_vat_rate=Decimal("0.00"),
            valorized_amount=Decimal("250.00"),
            scan_timestamp=now,
            branch_id=1,
            observation="Ingreso mercadería",
        ),
        GoodsReceivedRawRecord(
            audit_id=2,
            article_code="PERF01",
            affected_amount=2,
            applied_unit_cost=Decimal("100.00"),
            applied_vat_rate=Decimal("0.21"),
            valorized_amount=Decimal("242.00"),
            scan_timestamp=now,
            branch_id=1,
            observation="Ajuste por sobrante",
        ),
    ]

    async def get_article_side_effect(article_code, *args, **kwargs):
        if article_code == "MED01":
            return Articulo(
                id_articulo="MED01",
                des_articulo="Paracetamol 500mg",
                des_familia="Medicamentos",
                pcio_com_siva=Decimal("50.00"),
            )
        elif article_code == "PERF01":
            return Articulo(
                id_articulo="PERF01",
                des_articulo="Perfume Floral",
                des_familia="Perfumeria",
                pcio_com_siva=Decimal("100.00"),
            )
        return None

    async def get_barcode_side_effect(article_code, *args, **kwargs):
        if article_code == "MED01":
            return "7791234567890"
        elif article_code == "PERF01":
            return "7799876543210"
        return None

    mock_article_repo.get_by_id.side_effect = get_article_side_effect
    mock_article_repo.get_barcode_by_article_id.side_effect = get_barcode_side_effect

    filters = GoodsReceivedReportFilters(
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        default_vat_rate=Decimal("0.21"),
    )

    result = await report_service.get_goods_received_report(tenant_id="1", filters=filters)

    assert result.total_items == 2
    assert result.total_added_units == 7

    med_item = next(i for i in result.line_items if i.article_code == "MED01")
    assert med_item.barcode == "7791234567890"
    assert med_item.des_articulo == "Paracetamol 500mg"
    assert med_item.des_familia == "Medicamentos"
    assert med_item.reason == "Ingreso mercadería"
    assert med_item.quantity_added == 5
    assert med_item.pcio_com_siva == Decimal("50.00")
    assert med_item.vat_rate == Decimal("0.00")
    assert med_item.total_unit_cost == Decimal("50.00")
    assert med_item.capital_inyectado == Decimal("250.00")

    perf_item = next(i for i in result.line_items if i.article_code == "PERF01")
    assert perf_item.barcode == "7799876543210"
    assert perf_item.des_articulo == "Perfume Floral"
    assert perf_item.des_familia == "Perfumeria"
    assert perf_item.reason == "Ajuste por sobrante"
    assert perf_item.quantity_added == 2
    assert perf_item.pcio_com_siva == Decimal("100.00")
    assert perf_item.vat_rate == Decimal("0.21")
    assert perf_item.total_unit_cost == Decimal("121.00")
    assert perf_item.capital_inyectado == Decimal("242.00")

    assert result.total_capital_inyectado == Decimal("492.00")
    assert isinstance(result.total_capital_inyectado, Decimal)


@pytest.mark.asyncio
async def test_get_goods_received_report_consolidates_records_same_article_and_reason(
    report_service, mock_report_repo, mock_article_repo
):
    now = datetime(2026, 9, 10, 12, 0, 0)
    mock_report_repo.fetch_goods_received_records.return_value = [
        GoodsReceivedRawRecord(
            audit_id=10,
            article_code="ITEM_X",
            affected_amount=4,
            applied_unit_cost=Decimal("25.00"),
            applied_vat_rate=Decimal("0.21"),
            valorized_amount=Decimal("121.00"),
            scan_timestamp=now,
            branch_id=1,
            observation="Ingreso lote nuevo",
        ),
        GoodsReceivedRawRecord(
            audit_id=11,
            article_code="ITEM_X",
            affected_amount=6,
            applied_unit_cost=Decimal("25.00"),
            applied_vat_rate=Decimal("0.21"),
            valorized_amount=Decimal("181.50"),
            scan_timestamp=now,
            branch_id=1,
            observation="Ingreso lote nuevo",
        ),
    ]

    mock_article_repo.get_by_id.return_value = Articulo(
        id_articulo="ITEM_X",
        des_articulo="Alcohol en Gel 250ml",
        des_familia="Higiene",
        pcio_com_siva=Decimal("25.00"),
    )
    mock_article_repo.get_barcode_by_article_id.return_value = "7791112223334"

    filters = GoodsReceivedReportFilters(
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )

    result = await report_service.get_goods_received_report(tenant_id="1", filters=filters)

    assert result.total_items == 1
    assert result.total_added_units == 10
    item = result.line_items[0]
    assert item.barcode == "7791112223334"
    assert item.quantity_added == 10
    assert item.total_unit_cost == Decimal("30.25")
    assert item.capital_inyectado == Decimal("302.50")
    assert result.total_capital_inyectado == Decimal("302.50")


@pytest.mark.asyncio
async def test_get_goods_received_report_article_not_found_graceful(
    report_service, mock_report_repo, mock_article_repo
):
    now = datetime(2026, 9, 1, 10, 0, 0)
    mock_report_repo.fetch_goods_received_records.return_value = [
        GoodsReceivedRawRecord(
            audit_id=99,
            article_code="DESCONOCIDO",
            affected_amount=3,
            applied_unit_cost=Decimal("10.00"),
            applied_vat_rate=Decimal("0.21"),
            valorized_amount=Decimal("36.30"),
            scan_timestamp=now,
            branch_id=1,
            observation=None,
        )
    ]
    mock_article_repo.get_by_id.return_value = None
    mock_article_repo.get_barcode_by_article_id.return_value = None

    filters = GoodsReceivedReportFilters(
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
    )

    result = await report_service.get_goods_received_report(tenant_id="1", filters=filters)

    assert result.total_items == 1
    item = result.line_items[0]
    assert item.barcode == ""
    assert item.des_articulo == "Artículo desconocido"
    assert item.reason == "Ingreso / Alta"
    assert item.quantity_added == 3
    assert item.capital_inyectado == Decimal("0.00")


# ============================================================================
# FastAPI Endpoint Integration Tests (RBAC & Output Validation)
# ============================================================================

@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_goods_received_service():
    return AsyncMock(spec=GoodsReceivedReportService)


@pytest.fixture
def client():
    return TestClient(app)


def test_goods_received_report_forbidden_for_supervisor(client, mock_goods_received_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "supervisor@farmanor.com",
        "role": "supervisor",
        "tenant_id": "1",
        "id_usuario": 2,
    }
    app.dependency_overrides[get_goods_received_report_service] = lambda: mock_goods_received_service

    response = client.get(
        "/api/v1/reports/goods-received?start_date=2026-09-01&end_date=2026-09-30"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not permitted" in response.json()["detail"].lower()


def test_goods_received_report_forbidden_for_auditor(client, mock_goods_received_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@farmanor.com",
        "role": "auditor",
        "tenant_id": "1",
        "id_usuario": 3,
    }
    app.dependency_overrides[get_goods_received_report_service] = lambda: mock_goods_received_service

    response = client.get(
        "/api/v1/reports/goods-received?start_date=2026-09-01&end_date=2026-09-30"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not permitted" in response.json()["detail"].lower()


def test_goods_received_report_success_for_admin(client, mock_goods_received_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@farmanor.com",
        "role": "administrador",
        "tenant_id": "1",
        "id_usuario": 1,
    }

    mock_response = GoodsReceivedReportResponse(
        tenant_id="1",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        default_vat_rate=Decimal("0.21"),
        total_items=2,
        total_added_units=7,
        total_capital_inyectado=Decimal("492.00"),
        line_items=[
            GoodsReceivedLineItem(
                barcode="7791234567890",
                article_code="MED01",
                des_articulo="Paracetamol 500mg",
                des_familia="Medicamentos",
                reason="Ingreso mercadería",
                quantity_added=5,
                pcio_com_siva=Decimal("50.00"),
                vat_rate=Decimal("0.00"),
                total_unit_cost=Decimal("50.00"),
                capital_inyectado=Decimal("250.00"),
            ),
            GoodsReceivedLineItem(
                barcode="7799876543210",
                article_code="PERF01",
                des_articulo="Perfume Floral",
                des_familia="Perfumeria",
                reason="Ajuste por sobrante",
                quantity_added=2,
                pcio_com_siva=Decimal("100.00"),
                vat_rate=Decimal("0.21"),
                total_unit_cost=Decimal("121.00"),
                capital_inyectado=Decimal("242.00"),
            ),
        ],
    )
    mock_goods_received_service.get_goods_received_report.return_value = mock_response
    app.dependency_overrides[get_goods_received_report_service] = lambda: mock_goods_received_service

    response = client.get(
        "/api/v1/reports/goods-received?start_date=2026-09-01&end_date=2026-09-30"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tenant_id"] == "1"
    assert data["total_items"] == 2
    assert data["total_added_units"] == 7
    assert Decimal(str(data["total_capital_inyectado"])) == Decimal("492.00")
    assert len(data["line_items"]) == 2

    med = data["line_items"][0]
    assert med["barcode"] == "7791234567890"
    assert med["article_code"] == "MED01"
    assert med["reason"] == "Ingreso mercadería"
    assert Decimal(str(med["vat_rate"])) == Decimal("0.00")
    assert Decimal(str(med["capital_inyectado"])) == Decimal("250.00")

    perf = data["line_items"][1]
    assert perf["barcode"] == "7799876543210"
    assert perf["article_code"] == "PERF01"
    assert perf["reason"] == "Ajuste por sobrante"
    assert Decimal(str(perf["vat_rate"])) == Decimal("0.21")
    assert Decimal(str(perf["capital_inyectado"])) == Decimal("242.00")


def test_goods_received_report_invalid_date_range(client, mock_goods_received_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@farmanor.com",
        "role": "administrador",
        "tenant_id": "1",
        "id_usuario": 1,
    }
    app.dependency_overrides[get_goods_received_report_service] = lambda: mock_goods_received_service

    # start_date > end_date
    response = client.get(
        "/api/v1/reports/goods-received?start_date=2026-10-01&end_date=2026-09-01"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "start_date cannot be after end_date" in response.json()["detail"]


def test_goods_received_report_unauthenticated(client):
    response = client.get(
        "/api/v1/reports/goods-received?start_date=2026-09-01&end_date=2026-09-30"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
