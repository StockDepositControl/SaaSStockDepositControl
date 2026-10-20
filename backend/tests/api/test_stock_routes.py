import pytest
from unittest.mock import AsyncMock
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.dependencies.services import get_article_search_service, get_audit_service
from backend.app.articles.models import Articulo
from backend.app.movements.domain import StockPorDeposito, StockLookupResult
from backend.app.articles.services import ArticleSearchService
from backend.app.movements.services import AuditService
from backend.app.exceptions import EntityNotFoundException

@pytest.fixture
def mock_search_service():
    return AsyncMock(spec=ArticleSearchService)

@pytest.fixture
def mock_audit_service():
    # AuditService contains stock_repository and stock_lookup_service
    service = AsyncMock(spec=AuditService)
    service.stock_repository = AsyncMock()
    service.stock_lookup_service = AsyncMock()
    return service

def test_get_stock_position_admin_includes_cost(mock_search_service, mock_audit_service):
    from backend.api.v1.stock import require_audit_roles

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": "1",
        "id_usuario": 1
    }

    mock_article = Articulo(
        id_articulo="1042",
        presentacion="Caja x 20",
        des_articulo="Ibuprofeno 400mg",
        id_marca=1,
        des_marca="Bayer",
        id_familia="01",
        des_familia="Medicamentos",
        id_grupo="02",
        des_grupo="Analgésicos",
        pcio_com_siva=Decimal("150.00")
    )
    mock_search_service.get_article_by_id.return_value = mock_article
    
    mock_stock_pos = StockLookupResult(
        id_articulo="1042",
        stock_real=95,
        source="db_articles",
    )
    mock_audit_service.stock_lookup_service.get_effective_stock.return_value = mock_stock_pos

    app.dependency_overrides[get_article_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    # Query without id_sucursal and id_deposito, testing fallback to tenant_id=1
    response = client.get("/api/v1/stock/position?id_articulo=1042")

    assert response.status_code == 200
    data = response.json()
    assert data["des_articulo"] == "Ibuprofeno 400mg"
    assert data["stock_real"] == 95
    assert "id_articulo" not in data
    assert "stock_teorico" not in data
    assert "pcio_com_siva" in data
    assert Decimal(str(data["pcio_com_siva"])) == Decimal("150.00")

    app.dependency_overrides.clear()

def test_get_stock_position_auditor_hides_cost(mock_search_service, mock_audit_service):
    from backend.api.v1.stock import require_audit_roles

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "1",
        "id_usuario": 2
    }

    mock_article = Articulo(
        id_articulo="1042",
        des_articulo="Ibuprofeno 400mg",
        pcio_com_siva=Decimal("150.00")
    )
    mock_search_service.get_article_by_id.return_value = mock_article
    
    mock_stock_pos = StockLookupResult(
        id_articulo="1042",
        stock_real=95,
        source="db_articles",
    )
    mock_audit_service.stock_lookup_service.get_effective_stock.return_value = mock_stock_pos

    app.dependency_overrides[get_article_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    response = client.get("/api/v1/stock/position?id_articulo=1042&id_sucursal=1&id_deposito=1")

    assert response.status_code == 200
    data = response.json()
    assert data["stock_real"] == 95
    assert "pcio_com_siva" not in data

    app.dependency_overrides.clear()

def test_get_stock_position_not_found(mock_search_service, mock_audit_service):
    from backend.api.v1.stock import require_audit_roles

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": "1",
        "id_usuario": 1
    }

    mock_search_service.get_article_by_id.side_effect = EntityNotFoundException("Article not found")

    app.dependency_overrides[get_article_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    response = client.get("/api/v1/stock/position?id_articulo=nonexistent999&id_sucursal=1&id_deposito=1")

    assert response.status_code == 404
    app.dependency_overrides.clear()


def test_get_stock_position_alphanumeric_tenant(mock_search_service, mock_audit_service):
    from backend.api.v1.stock import require_audit_roles

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": "tenant-uuid-xyz-123",
        "id_usuario": 1
    }

    mock_article = Articulo(
        id_articulo="1042",
        des_articulo="Ibuprofeno 400mg",
        pcio_com_siva=Decimal("150.00")
    )
    mock_search_service.get_article_by_id.return_value = mock_article
    mock_audit_service.stock_lookup_service.get_effective_stock.return_value = StockLookupResult(
        id_articulo="1042", stock_real=95, source="db_articles"
    )

    app.dependency_overrides[get_article_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    # Query without branch/deposito parameters, testing that string tenant_id does not throw ValueError
    response = client.get("/api/v1/stock/position?id_articulo=1042")

    assert response.status_code == 200
    data = response.json()
    assert data["id_sucursal"] == 1
    assert data["id_deposito"] == 1

    app.dependency_overrides.clear()


def test_post_single_audit_endpoint(mock_audit_service):
    from backend.api.v1.stock import require_audit_roles
    from backend.app.movements.schemas import AuditEntryResult
    from backend.app.movements.domain import TipoAccion

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "1",
        "branch_id": 1,
        "id_usuario": 5,
    }

    mock_audit_service.register_single_audit.return_value = AuditEntryResult(
        client_uuid="uuid-123",
        id_articulo="1042",
        stock_real=100,
        stock_fisico_contado=90,
        delta_stock=-10,
        tipo_accion=TipoAccion.BAJA,
        cantidad_afectada=10,
        audit_quantity=90,
        monto_valorizado=Decimal("1500.0000"),
        audit_id=42,
    )
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    response = client.post(
        "/api/v1/stock/audit",
        json={
            "id_deposito": 1,
            "id_articulo": "1042",
            "stock_fisico_contado": 90,
            "observation": "Daily audit",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["client_uuid"] == "uuid-123"
    assert data["audit_id"] == 42
    assert data["delta_stock"] == -10

    app.dependency_overrides.clear()


def test_post_single_audit_no_active_session_409(mock_audit_service):
    from backend.api.v1.stock import require_audit_roles
    from backend.app.exceptions import NoActiveWorkSessionError

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "1",
        "branch_id": 1,
        "id_usuario": 5,
    }

    mock_audit_service.register_single_audit.side_effect = NoActiveWorkSessionError("No active work session found for branch '1'.")
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    response = client.post(
        "/api/v1/stock/audit",
        json={
            "id_sucursal": 1,
            "id_deposito": 1,
            "id_articulo": "1042",
            "stock_fisico_contado": 90,
        },
    )

    assert response.status_code == 409
    data = response.json()
    assert data["error_type"] == "NoActiveWorkSession"
    assert "No active work session" in data["detail"]

    app.dependency_overrides.clear()


def test_post_batch_audit_endpoint(mock_audit_service):
    from backend.api.v1.stock import require_audit_roles
    from backend.app.movements.schemas import AuditBatchResult, AuditEntryResult
    from backend.app.movements.domain import TipoAccion

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "1",
        "user_id": 5,
    }

    mock_audit_service.register_batch_audit.return_value = AuditBatchResult(
        results=[
            AuditEntryResult(
                client_uuid="uuid-456",
                id_articulo="1042",
                stock_real=100,
                stock_fisico_contado=95,
                delta_stock=-5,
                tipo_accion=TipoAccion.BAJA,
                cantidad_afectada=5,
                audit_quantity=95,
                monto_valorizado=Decimal("750.0000"),
                audit_id=43,
            )
        ],
        total_processed=1,
        duplicates_skipped=0,
    )
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    response = client.post(
        "/api/v1/stock/audit/batch",
        json={
            "items": [
                {
                    "id_sucursal": 1,
                    "id_deposito": 1,
                    "id_articulo": "1042",
                    "stock_fisico_contado": 95,
                }
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 1
    assert len(data["results"]) == 1

    app.dependency_overrides.clear()


def test_post_single_audit_defaults_omitted_deposit_and_branch(mock_audit_service):
    from backend.api.v1.stock import require_audit_roles
    from backend.app.movements.schemas import AuditEntryResult
    from backend.app.movements.domain import TipoAccion

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "1",
        "branch_id": 2,
        "id_usuario": 5,
    }

    mock_audit_service.register_single_audit.return_value = AuditEntryResult(
        client_uuid="uuid-fallback-1",
        id_articulo="1042",
        stock_real=100,
        stock_fisico_contado=90,
        delta_stock=-10,
        tipo_accion=TipoAccion.BAJA,
        cantidad_afectada=10,
        audit_quantity=90,
        monto_valorizado=Decimal("1500.0000"),
        audit_id=101,
    )
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    response = client.post(
        "/api/v1/stock/audit",
        json={
            "id_articulo": "1042",
            "stock_fisico_contado": 90,
            "observation": "Omitted branch and deposit",
        },
    )

    assert response.status_code == 201
    call_args = mock_audit_service.register_single_audit.call_args
    assert call_args is not None
    effective_entry = call_args.kwargs["entry"]
    assert effective_entry.id_sucursal == 2
    assert effective_entry.id_deposito == 1

    app.dependency_overrides.clear()


def test_post_single_audit_defaults_branch_when_claim_missing(mock_audit_service):
    from backend.api.v1.stock import require_audit_roles
    from backend.app.movements.schemas import AuditEntryResult
    from backend.app.movements.domain import TipoAccion

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "1",
        "id_usuario": 5,
    }

    mock_audit_service.register_single_audit.return_value = AuditEntryResult(
        client_uuid="uuid-fallback-2",
        id_articulo="1042",
        stock_real=100,
        stock_fisico_contado=90,
        delta_stock=-10,
        tipo_accion=TipoAccion.BAJA,
        cantidad_afectada=10,
        audit_quantity=90,
        monto_valorizado=Decimal("1500.0000"),
        audit_id=102,
    )
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    response = client.post(
        "/api/v1/stock/audit",
        json={
            "id_articulo": "1042",
            "stock_fisico_contado": 90,
        },
    )

    assert response.status_code == 201
    call_args = mock_audit_service.register_single_audit.call_args
    assert call_args is not None
    effective_entry = call_args.kwargs["entry"]
    assert effective_entry.id_sucursal == 1
    assert effective_entry.id_deposito == 1

    app.dependency_overrides.clear()


def test_post_single_audit_preserves_explicit_ids(mock_audit_service):
    from backend.api.v1.stock import require_audit_roles
    from backend.app.movements.schemas import AuditEntryResult
    from backend.app.movements.domain import TipoAccion

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "1",
        "branch_id": 1,
        "id_usuario": 5,
    }

    mock_audit_service.register_single_audit.return_value = AuditEntryResult(
        client_uuid="uuid-explicit",
        id_articulo="1042",
        stock_real=100,
        stock_fisico_contado=90,
        delta_stock=-10,
        tipo_accion=TipoAccion.BAJA,
        cantidad_afectada=10,
        audit_quantity=90,
        monto_valorizado=Decimal("1500.0000"),
        audit_id=103,
    )
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    response = client.post(
        "/api/v1/stock/audit",
        json={
            "id_sucursal": 3,
            "id_deposito": 2,
            "id_articulo": "1042",
            "stock_fisico_contado": 90,
        },
    )

    assert response.status_code == 201
    call_args = mock_audit_service.register_single_audit.call_args
    assert call_args is not None
    effective_entry = call_args.kwargs["entry"]
    assert effective_entry.id_sucursal == 3
    assert effective_entry.id_deposito == 2

    app.dependency_overrides.clear()


def test_post_batch_audit_defaults_omitted_deposit_and_branch(mock_audit_service):
    from backend.api.v1.stock import require_audit_roles
    from backend.app.movements.schemas import AuditBatchResult, AuditEntryResult
    from backend.app.movements.domain import TipoAccion

    app.dependency_overrides[require_audit_roles] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "1",
        "branch_id": 4,
        "user_id": 5,
    }

    mock_audit_service.register_batch_audit.return_value = AuditBatchResult(
        results=[
            AuditEntryResult(
                client_uuid="uuid-b1",
                id_articulo="1042",
                stock_real=100,
                stock_fisico_contado=95,
                delta_stock=-5,
                tipo_accion=TipoAccion.BAJA,
                cantidad_afectada=5,
                audit_quantity=95,
                monto_valorizado=Decimal("750.0000"),
                audit_id=104,
            ),
            AuditEntryResult(
                client_uuid="uuid-b2",
                id_articulo="1043",
                stock_real=50,
                stock_fisico_contado=50,
                delta_stock=0,
                tipo_accion=TipoAccion.SIN_ACCION,
                cantidad_afectada=0,
                audit_quantity=50,
                monto_valorizado=Decimal("0.0000"),
                audit_id=105,
            ),
        ],
        total_processed=2,
        duplicates_skipped=0,
    )
    app.dependency_overrides[get_audit_service] = lambda: mock_audit_service

    client = TestClient(app)
    response = client.post(
        "/api/v1/stock/audit/batch",
        json={
            "items": [
                {
                    "id_articulo": "1042",
                    "stock_fisico_contado": 95,
                },
                {
                    "id_sucursal": 5,
                    "id_deposito": 3,
                    "id_articulo": "1043",
                    "stock_fisico_contado": 50,
                },
            ]
        },
    )

    assert response.status_code == 200
    call_args = mock_audit_service.register_batch_audit.call_args
    assert call_args is not None
    effective_batch = call_args.kwargs["batch"]
    assert len(effective_batch.items) == 2
    assert effective_batch.items[0].id_sucursal == 4
    assert effective_batch.items[0].id_deposito == 1
    assert effective_batch.items[1].id_sucursal == 5
    assert effective_batch.items[1].id_deposito == 3

    app.dependency_overrides.clear()




