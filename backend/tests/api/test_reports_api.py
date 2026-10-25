from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from backend.api.dependencies.auth import get_current_user_claims
from backend.api.dependencies.services import get_daily_inventory_balance_report_service
from backend.api.main import app
from backend.app.reports.schemas import (
    DailyInventoryBalanceResponse,
    DailyInventoryBalanceSummary,
)
from backend.app.reports.services import DailyInventoryBalanceReportService
from fastapi import status
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_balance_service():
    return AsyncMock(spec=DailyInventoryBalanceReportService)


@pytest.fixture
def client():
    return TestClient(app)


def test_inventory_balance_unauthenticated(client):
    response = client.get(
        "/api/v1/reports/inventory-balance?start_date=2026-01-01&end_date=2026-01-31"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_inventory_balance_forbidden_for_supervisor(client, mock_balance_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "supervisor@farmanor.com",
        "role": "supervisor",
        "tenant_id": "1",
        "id_usuario": 2,
    }
    app.dependency_overrides[get_daily_inventory_balance_report_service] = lambda: (
        mock_balance_service
    )

    response = client.get(
        "/api/v1/reports/inventory-balance?start_date=2026-01-01&end_date=2026-01-31"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not permitted" in response.json()["detail"].lower()


def test_inventory_balance_forbidden_for_auditor(client, mock_balance_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@farmanor.com",
        "role": "auditor",
        "tenant_id": "1",
        "id_usuario": 3,
    }
    app.dependency_overrides[get_daily_inventory_balance_report_service] = lambda: (
        mock_balance_service
    )

    response = client.get(
        "/api/v1/reports/inventory-balance?start_date=2026-01-01&end_date=2026-01-31"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not permitted" in response.json()["detail"].lower()


def test_inventory_balance_invalid_date_range(client, mock_balance_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@farmanor.com",
        "role": "administrador",
        "tenant_id": "1",
        "id_usuario": 1,
    }
    app.dependency_overrides[get_daily_inventory_balance_report_service] = lambda: (
        mock_balance_service
    )

    # start_date > end_date
    response = client.get(
        "/api/v1/reports/inventory-balance?start_date=2026-02-01&end_date=2026-01-01"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "start_date cannot be after end_date" in response.json()["detail"]


def test_inventory_balance_success_for_admin(client, mock_balance_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@farmanor.com",
        "role": "administrador",
        "tenant_id": "1",
        "id_usuario": 1,
    }

    mock_response = DailyInventoryBalanceResponse(
        tenant_id="1",
        branch_id=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        total_days=1,
        total_addition_value=Decimal("250000.00"),
        total_shrinkage_value=Decimal("45000.00"),
        net_patrimonial_variation=Decimal("205000.00"),
        daily_summaries=[
            DailyInventoryBalanceSummary(
                report_date=date(2026, 1, 15),
                total_audit_articles=50,
                total_processed_units=1200,
                total_addition_units=800,
                total_shrinkage_units=150,
                total_addition_value=Decimal("250000.00"),
                total_shrinkage_value=Decimal("45000.00"),
                net_patrimonial_variation=Decimal("205000.00"),
            )
        ],
    )
    mock_balance_service.get_daily_inventory_balance_report.return_value = mock_response
    app.dependency_overrides[get_daily_inventory_balance_report_service] = lambda: (
        mock_balance_service
    )

    response = client.get(
        "/api/v1/reports/inventory-balance?start_date=2026-01-01&end_date=2026-01-31&branch_id=1"
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tenant_id"] == "1"
    assert data["branch_id"] == 1
    assert data["start_date"] == "2026-01-01"
    assert data["end_date"] == "2026-01-31"
    assert data["total_days"] == 1
    assert Decimal(str(data["total_addition_value"])) == Decimal("250000.00")
    assert Decimal(str(data["total_shrinkage_value"])) == Decimal("45000.00")
    assert Decimal(str(data["net_patrimonial_variation"])) == Decimal("205000.00")
    assert len(data["daily_summaries"]) == 1

    summary = data["daily_summaries"][0]
    assert summary["report_date"] == "2026-01-15"
    assert summary["total_audit_articles"] == 50
    assert summary["total_processed_units"] == 1200
    assert summary["total_addition_units"] == 800
    assert summary["total_shrinkage_units"] == 150
    assert Decimal(str(summary["total_addition_value"])) == Decimal("250000.00")
    assert Decimal(str(summary["total_shrinkage_value"])) == Decimal("45000.00")
    assert Decimal(str(summary["net_patrimonial_variation"])) == Decimal("205000.00")
