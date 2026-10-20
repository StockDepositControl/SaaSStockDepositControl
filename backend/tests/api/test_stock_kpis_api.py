import pytest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.v1.stock import require_audit_roles
from backend.api.dependencies.services import get_stock_kpi_service, get_work_session_service
from backend.app.movements.schemas import DashboardKPIsPublicOut, DashboardKPIsResponse
from backend.app.movements.services import StockKPIService
from backend.app.work_sessions.services import WorkSessionService

BASE = dict(
    total_articulos=200,
    auditados=50,
    pendientes=150,
    porcentaje_avance=25,
    discrepancias_alta=4,
    discrepancias_baja=6,
    sin_accion=40,
    out_of_stock_count=7,
)


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _override(role: str, payload):
    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": f"{role}@example.com",
        "role": role,
        "tenant_id": "1",
        "branch_id": 1,
        "id_usuario": 1,
    }
    service = AsyncMock(spec=StockKPIService)
    service.get_dashboard_kpis.return_value = payload
    ws = AsyncMock(spec=WorkSessionService)
    ws.get_or_create_active_session.return_value = SimpleNamespace(session_id=77)
    app.dependency_overrides[get_stock_kpi_service] = lambda: service
    app.dependency_overrides[get_work_session_service] = lambda: ws
    return service


def test_admin_receives_valorized_amounts():
    payload = DashboardKPIsResponse(
        **BASE,
        monto_valorizado_baja=Decimal("123.45"),
        monto_valorizado_alta=Decimal("10.00"),
    )
    service = _override("administrador", payload)

    response = TestClient(app).get("/api/v1/stock/kpis?id_deposito=2")

    assert response.status_code == 200
    data = response.json()
    assert data["out_of_stock_count"] == 7
    assert Decimal(str(data["monto_valorizado_baja"])) == Decimal("123.45")
    kwargs = service.get_dashboard_kpis.await_args.kwargs
    assert kwargs["is_admin"] is True
    assert kwargs["deposit_id"] == 2
    assert kwargs["session_id"] == 77


@pytest.mark.parametrize("role", ["auditor", "supervisor"])
def test_non_admin_payload_has_no_financial_keys(role):
    service = _override(role, DashboardKPIsPublicOut(**BASE))

    response = TestClient(app).get("/api/v1/stock/kpis")

    assert response.status_code == 200
    data = response.json()
    assert data["total_articulos"] == 200
    assert "monto_valorizado_baja" not in data
    assert "monto_valorizado_alta" not in data
    assert service.get_dashboard_kpis.await_args.kwargs["is_admin"] is False


def test_invalid_deposit_rejected():
    _override("administrador", DashboardKPIsPublicOut(**BASE))

    response = TestClient(app).get("/api/v1/stock/kpis?id_deposito=0")

    assert response.status_code == 422


def test_requires_authentication():
    response = TestClient(app).get("/api/v1/stock/kpis")

    assert response.status_code in (401, 403)
