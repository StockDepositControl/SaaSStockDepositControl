from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from backend.api.dependencies.auth import get_current_user_claims
from backend.api.dependencies.services import get_shrinkage_report_service
from backend.api.main import app
from backend.app.reports.schemas import (
    ShrinkageLineItem,
    ShrinkageReportResponse,
)
from backend.app.reports.services import ShrinkageReportService


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_shrinkage_service():
    return AsyncMock(spec=ShrinkageReportService)


@pytest.fixture
def client():
    return TestClient(app)


def test_shrinkage_report_forbidden_for_supervisor(client, mock_shrinkage_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "supervisor@farmanor.com",
        "role": "supervisor",
        "tenant_id": "1",
        "id_usuario": 2,
    }
    app.dependency_overrides[get_shrinkage_report_service] = lambda: mock_shrinkage_service

    response = client.get(
        "/api/v1/reports/shrinkage?start_date=2026-01-01&end_date=2026-01-31"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not permitted" in response.json()["detail"].lower()


def test_shrinkage_report_forbidden_for_auditor(client, mock_shrinkage_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@farmanor.com",
        "role": "auditor",
        "tenant_id": "1",
        "id_usuario": 3,
    }
    app.dependency_overrides[get_shrinkage_report_service] = lambda: mock_shrinkage_service

    response = client.get(
        "/api/v1/reports/shrinkage?start_date=2026-01-01&end_date=2026-01-31"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not permitted" in response.json()["detail"].lower()


def test_shrinkage_report_success_for_admin(client, mock_shrinkage_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@farmanor.com",
        "role": "administrador",
        "tenant_id": "1",
        "id_usuario": 1,
    }

    mock_response = ShrinkageReportResponse(
        tenant_id="1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        default_vat_rate=Decimal("0.21"),
        total_items=2,
        total_shrinkage_units=7,
        total_financial_erosion=Decimal("563.00"),
        line_items=[
            ShrinkageLineItem(
                article_code="MED01",
                des_articulo="Ibuprofeno 400mg",
                des_familia="Medicamentos",
                pcio_com_siva=Decimal("50.00"),
                vat_rate=Decimal("0.00"),
                total_unit_cost=Decimal("50.00"),
                total_quantity=4,
                total_financial_loss=Decimal("200.00"),
            ),
            ShrinkageLineItem(
                article_code="PERF01",
                des_articulo="Shampoo Anticaspa",
                des_familia="Perfumeria",
                pcio_com_siva=Decimal("100.00"),
                vat_rate=Decimal("0.21"),
                total_unit_cost=Decimal("121.00"),
                total_quantity=3,
                total_financial_loss=Decimal("363.00"),
            ),
        ],
    )
    mock_shrinkage_service.get_shrinkage_report.return_value = mock_response
    app.dependency_overrides[get_shrinkage_report_service] = lambda: mock_shrinkage_service

    response = client.get(
        "/api/v1/reports/shrinkage?start_date=2026-01-01&end_date=2026-01-31"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tenant_id"] == "1"
    assert data["total_items"] == 2
    assert data["total_shrinkage_units"] == 7
    assert Decimal(str(data["total_financial_erosion"])) == Decimal("563.00")
    assert len(data["line_items"]) == 2

    med = data["line_items"][0]
    assert med["article_code"] == "MED01"
    assert Decimal(str(med["vat_rate"])) == Decimal("0.00")
    assert Decimal(str(med["total_financial_loss"])) == Decimal("200.00")

    perf = data["line_items"][1]
    assert perf["article_code"] == "PERF01"
    assert Decimal(str(perf["vat_rate"])) == Decimal("0.21")
    assert Decimal(str(perf["total_financial_loss"])) == Decimal("363.00")


def test_shrinkage_report_invalid_date_range(client, mock_shrinkage_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@farmanor.com",
        "role": "administrador",
        "tenant_id": "1",
        "id_usuario": 1,
    }
    app.dependency_overrides[get_shrinkage_report_service] = lambda: mock_shrinkage_service

    # start_date > end_date
    response = client.get(
        "/api/v1/reports/shrinkage?start_date=2026-02-01&end_date=2026-01-01"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "start_date cannot be after end_date" in response.json()["detail"]


def test_shrinkage_report_unauthenticated(client):
    response = client.get(
        "/api/v1/reports/shrinkage?start_date=2026-01-01&end_date=2026-01-31"
    )
    # Without token/claims override, should return 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
