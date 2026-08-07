import pytest
from unittest.mock import AsyncMock
from decimal import Decimal
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.dependencies.services import get_article_search_service
from backend.app.articles.models import Articulo
from backend.app.articles.services import ArticleSearchService

@pytest.fixture
def mock_search_service():
    service = AsyncMock(spec=ArticleSearchService)
    return service

def test_search_articles_endpoint_as_admin(mock_search_service, monkeypatch):
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


def test_search_articles_endpoint_as_auditor(mock_search_service):
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

    client = TestClient(app)
    response = client.get("/api/v1/articles/search?query=Ibuprofeno")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id_articulo"] == "1042"
    # Auditor must NOT get cost field pcio_com_siva
    assert "pcio_com_siva" not in data[0]

    app.dependency_overrides.clear()
