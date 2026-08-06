import pytest
from unittest.mock import AsyncMock
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.dependencies.services import get_article_search_service, get_audit_service
from backend.app.articles.models import Articulo
from backend.app.movements.models import StockPorDeposito
from backend.app.movements.models import StockPorDeposito, StockLookupResult
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

