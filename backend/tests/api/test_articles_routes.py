import pytest
from unittest.mock import AsyncMock
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.dependencies.services import get_article_search_service, get_work_session_service
from backend.app.articles.models import Articulo
from backend.app.articles.services import ArticleSearchService
from backend.app.work_sessions.services import WorkSessionService
from backend.app.work_sessions.models import WorkSession
from datetime import datetime, timezone

@pytest.fixture
def mock_search_service():
    service = AsyncMock(spec=ArticleSearchService)
    return service

@pytest.fixture
def mock_work_session_service():
    class MockService:
        async def get_or_create_active_session(self, *args, **kwargs):
            return WorkSession(
                session_id=1,
                tenant_id=1,
                branch_id=1,
                opened_at=datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
                status="OPEN"
            )
    return MockService()

def test_search_articles_endpoint_as_admin(mock_search_service, mock_work_session_service, monkeypatch):
    from backend.api.dependencies.auth import get_current_user_claims

    # Mock user claims for Administrator role
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": "tenant-01"
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
    mock_search_service.search_articles.return_value = [mock_article]
    app.dependency_overrides[get_article_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_work_session_service] = lambda: mock_work_session_service

    client = TestClient(app)
    response = client.get("/api/v1/articles/search?query=Ibuprofeno")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id_articulo"] == "1042"
    assert data[0]["des_articulo"] == "Ibuprofeno 400mg"
    # Admin gets cost field pcio_com_siva
    assert "pcio_com_siva" in data[0]
    assert Decimal(str(data[0]["pcio_com_siva"])) == Decimal("150.00")

    app.dependency_overrides.clear()


def test_search_articles_endpoint_as_auditor(mock_search_service, mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims

    # Mock user claims for Auditor role
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "tenant-01"
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
    mock_search_service.search_articles.return_value = [mock_article]
    app.dependency_overrides[get_article_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_work_session_service] = lambda: mock_work_session_service

    client = TestClient(app)
    response = client.get("/api/v1/articles/search?query=Ibuprofeno")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id_articulo"] == "1042"
    # Auditor must NOT get cost field pcio_com_siva
    assert "pcio_com_siva" not in data[0]

    app.dependency_overrides.clear()


def test_get_all_articles_as_admin(mock_search_service, mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": "tenant-01"
    }

    mock_articles = [
        Articulo(
            id_articulo="1001",
            des_articulo="Aspirina 500mg",
            pcio_com_siva=Decimal("100.00")
        ),
        Articulo(
            id_articulo="1002",
            des_articulo="Paracetamol 500mg",
            pcio_com_siva=Decimal("120.00")
        ),
    ]
    # Use the appropriate method on the mock
    mock_search_service.get_article_by_id.return_value = mock_articles[0]
    app.dependency_overrides[get_article_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_work_session_service] = lambda: mock_work_session_service

    client = TestClient(app)
    response = client.get("/api/v1/articles/all")

    assert response.status_code == 200
    data = response.json()
    assert data["id_articulo"] == "1001"
    assert "pcio_com_siva" in data
    assert Decimal(str(data["pcio_com_siva"])) == Decimal("100.00")

    app.dependency_overrides.clear()


def test_get_all_articles_as_auditor(mock_search_service, mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "tenant-01"
    }

    mock_articles = [
        Articulo(
            id_articulo="1001",
            des_articulo="Aspirina 500mg",
            pcio_com_siva=Decimal("100.00")
        ),
    ]
    mock_search_service.get_article_by_id.return_value = mock_articles[0]
    app.dependency_overrides[get_article_search_service] = lambda: mock_search_service
    app.dependency_overrides[get_work_session_service] = lambda: mock_work_session_service

    client = TestClient(app)
    response = client.get("/api/v1/articles/all")

    assert response.status_code == 200
    data = response.json()
    assert data["id_articulo"] == "1001"
    assert "pcio_com_siva" not in data

    app.dependency_overrides.clear()


def test_instantiate_sqlalchemy_article_repository():
    from backend.adapters.repositories.article_repository import SQLAlchemyArticleRepository
    # Verify that the repository class is concrete and can be instantiated without TypeError
    repo = SQLAlchemyArticleRepository(session_factory=AsyncMock(), analytics_session_factory=AsyncMock())
    assert repo is not None


def test_list_articles_endpoint_as_admin_with_stock(mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims
    from backend.api.dependencies.services import get_article_catalog_orchestrator
    from backend.app.articles.orchestrator import ArticleCatalogOrchestrator

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": "tenant-01",
        "branch_id": 1,
    }

    mock_orchestrator = AsyncMock(spec=ArticleCatalogOrchestrator)
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
        pcio_com_siva=Decimal("150.00"),
        fue_auditado=False,
        stock_real=42,
    )
    mock_orchestrator.get_enriched_catalog.return_value = ([mock_article], 1)
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_work_session_service] = lambda: mock_work_session_service

    client = TestClient(app)
    response = client.get("/api/v1/articles?page=1&limit=50&id_deposito=1")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["limit"] == 50
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["id_articulo"] == "1042"
    assert item["stock_real"] == 42
    # Admin MUST have pcio_com_siva
    assert "pcio_com_siva" in item
    assert Decimal(str(item["pcio_com_siva"])) == Decimal("150.00")

    app.dependency_overrides.clear()


def test_list_articles_endpoint_as_auditor_with_stock_masked(mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims
    from backend.api.dependencies.services import get_article_catalog_orchestrator
    from backend.app.articles.orchestrator import ArticleCatalogOrchestrator

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": "tenant-01",
        "branch_id": 1,
    }

    mock_orchestrator = AsyncMock(spec=ArticleCatalogOrchestrator)
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
        pcio_com_siva=Decimal("150.00"),
        fue_auditado=False,
        stock_real=42,
    )
    mock_orchestrator.get_enriched_catalog.return_value = ([mock_article], 1)
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: mock_orchestrator
    app.dependency_overrides[get_work_session_service] = lambda: mock_work_session_service

    client = TestClient(app)
    response = client.get("/api/v1/articles?page=1&limit=50&id_deposito=1")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["id_articulo"] == "1042"
    assert item["stock_real"] == 42
    # Auditor must NOT have pcio_com_siva (structurally masked)
    assert "pcio_com_siva" not in item

    app.dependency_overrides.clear()

