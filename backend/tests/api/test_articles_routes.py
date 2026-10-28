from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from backend.api.dependencies.services import (
    get_article_catalog_orchestrator,
    get_article_search_service,
    get_work_session_service,
)
from backend.api.main import app
from backend.app.articles.models import Articulo
from backend.app.articles.orchestrator import ArticleCatalogOrchestrator
from backend.app.articles.services import ArticleSearchService
from backend.app.work_sessions.models import WorkSession
from fastapi.testclient import TestClient


@pytest.fixture
def mock_search_service():
    service = AsyncMock(spec=ArticleSearchService)
    return service


@pytest.fixture
def mock_orchestrator():
    return AsyncMock(spec=ArticleCatalogOrchestrator)


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
                status="OPEN",
            )

    return MockService()


def test_search_articles_endpoint_as_admin(
    mock_orchestrator, mock_work_session_service
):
    from backend.api.dependencies.auth import get_current_user_claims

    # Mock user claims for Administrator role
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": 1,
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
        pcio_com_siva=Decimal("150.00"),
        stock_real=194,
    )
    mock_orchestrator.search_and_enrich_articles.return_value = [mock_article]
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

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
    assert data[0]["stock_real"] == 194
    mock_orchestrator.search_and_enrich_articles.assert_awaited_once_with(
        query="Ibuprofeno", deposit_id=1, active_session_id=1, tenant_id=1
    )

    app.dependency_overrides.clear()


def test_search_articles_endpoint_as_auditor(
    mock_orchestrator, mock_work_session_service
):
    from backend.api.dependencies.auth import get_current_user_claims

    # Mock user claims for Auditor role
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": 1,
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
        pcio_com_siva=Decimal("150.00"),
        stock_real=194,
    )
    mock_orchestrator.search_and_enrich_articles.return_value = [mock_article]
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

    client = TestClient(app)
    response = client.get("/api/v1/articles/search?query=Ibuprofeno")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id_articulo"] == "1042"
    # Auditor must NOT get cost field pcio_com_siva
    assert "pcio_com_siva" not in data[0]
    assert data[0]["stock_real"] == 194

    app.dependency_overrides.clear()


def test_search_articles_forwards_id_deposito(
    mock_orchestrator, mock_work_session_service
):
    from backend.api.dependencies.auth import get_current_user_claims

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": 1,
    }
    mock_orchestrator.search_and_enrich_articles.return_value = []
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

    client = TestClient(app)
    response = client.get("/api/v1/articles/search?query=Ibu&id_deposito=3")
    invalid = client.get("/api/v1/articles/search?query=Ibu&id_deposito=0")

    assert response.status_code == 200
    assert response.json() == []
    mock_orchestrator.search_and_enrich_articles.assert_awaited_once_with(
        query="Ibu", deposit_id=3, active_session_id=1, tenant_id=1
    )
    assert invalid.status_code == 422

    app.dependency_overrides.clear()


def _override_search_deps(role, mock_orchestrator, mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": f"{role}@example.com",
        "role": role,
        "tenant_id": 1,
    }
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )


def _audited_article():
    return Articulo(
        id_articulo="ART-00002",
        presentacion="Caja x 30",
        des_articulo="MED Esasomeprazol 20mg",
        id_marca=3,
        des_marca="Roemmers",
        id_familia="01",
        des_familia="Medicamentos",
        id_grupo="03",
        des_grupo="Gastro",
        pcio_com_siva=Decimal("90.00"),
        stock_real=195,
        fue_auditado=True,
    )


def test_search_articles_audited_article_returns_session_count(
    mock_orchestrator, mock_work_session_service
):
    _override_search_deps("auditor", mock_orchestrator, mock_work_session_service)
    mock_orchestrator.search_and_enrich_articles.return_value = [_audited_article()]

    response = TestClient(app).get("/api/v1/articles/search?query=MED+Esa")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["stock_real"] == 195
    assert data[0]["fue_auditado"] is True
    assert "pcio_com_siva" not in data[0]

    app.dependency_overrides.clear()


def test_search_articles_endpoint_as_supervisor_masks_cost(
    mock_orchestrator, mock_work_session_service
):
    _override_search_deps("supervisor", mock_orchestrator, mock_work_session_service)
    mock_orchestrator.search_and_enrich_articles.return_value = [_audited_article()]

    response = TestClient(app).get("/api/v1/articles/search?query=MED+Esa")

    assert response.status_code == 200
    data = response.json()
    assert "pcio_com_siva" not in data[0]
    assert data[0]["stock_real"] == 195

    app.dependency_overrides.clear()


def test_search_articles_no_matches_returns_empty_list(
    mock_orchestrator, mock_work_session_service
):
    _override_search_deps("auditor", mock_orchestrator, mock_work_session_service)
    mock_orchestrator.search_and_enrich_articles.return_value = []

    response = TestClient(app).get("/api/v1/articles/search?query=nonexistent")

    assert response.status_code == 200
    assert response.json() == []
    mock_orchestrator.search_and_enrich_articles.assert_awaited_once_with(
        query="nonexistent", deposit_id=1, active_session_id=1, tenant_id=1
    )

    app.dependency_overrides.clear()


def test_get_article_by_id_endpoint_as_admin_with_stock(mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims
    from backend.api.dependencies.services import get_article_catalog_orchestrator
    from backend.app.articles.orchestrator import ArticleCatalogOrchestrator

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": 1,
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
        stock_real=25,
    )
    mock_orchestrator.get_enriched_article.return_value = mock_article
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

    client = TestClient(app)
    response = client.get("/api/v1/articles/1042?id_deposito=2")

    assert response.status_code == 200
    data = response.json()
    assert data["id_articulo"] == "1042"
    assert data["stock_real"] == 25
    assert "pcio_com_siva" in data
    assert Decimal(str(data["pcio_com_siva"])) == Decimal("150.00")

    mock_orchestrator.get_enriched_article.assert_called_once_with(
        id_articulo="1042",
        deposit_id=2,
        active_session_id=1,
        tenant_id=1,
    )

    app.dependency_overrides.clear()


def test_get_article_by_id_endpoint_as_auditor_with_stock_masked(
    mock_work_session_service,
):
    from backend.api.dependencies.auth import get_current_user_claims
    from backend.api.dependencies.services import get_article_catalog_orchestrator
    from backend.app.articles.orchestrator import ArticleCatalogOrchestrator

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": 1,
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
        stock_real=25,
    )
    mock_orchestrator.get_enriched_article.return_value = mock_article
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

    client = TestClient(app)
    response = client.get("/api/v1/articles/1042?id_deposito=3")

    assert response.status_code == 200
    data = response.json()
    assert data["id_articulo"] == "1042"
    assert data["stock_real"] == 25
    assert "pcio_com_siva" not in data

    mock_orchestrator.get_enriched_article.assert_called_once_with(
        id_articulo="1042",
        deposit_id=3,
        active_session_id=1,
        tenant_id=1,
    )

    app.dependency_overrides.clear()


def test_get_article_by_id_default_deposit(mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims
    from backend.api.dependencies.services import get_article_catalog_orchestrator
    from backend.app.articles.orchestrator import ArticleCatalogOrchestrator

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": 1,
        "branch_id": 1,
    }

    mock_orchestrator = AsyncMock(spec=ArticleCatalogOrchestrator)
    mock_article = Articulo(
        id_articulo="1042",
        des_articulo="Ibuprofeno 400mg",
        pcio_com_siva=Decimal("150.00"),
        stock_real=10,
    )
    mock_orchestrator.get_enriched_article.return_value = mock_article
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

    client = TestClient(app)
    response = client.get("/api/v1/articles/1042")

    assert response.status_code == 200
    mock_orchestrator.get_enriched_article.assert_called_once_with(
        id_articulo="1042",
        deposit_id=1,
        active_session_id=1,
        tenant_id=1,
    )

    app.dependency_overrides.clear()


def test_instantiate_sqlalchemy_article_repository():
    from backend.adapters.repositories.article_repository import (
        SQLAlchemyArticleRepository,
    )

    # Verify that the repository class is concrete and can be instantiated without
    # TypeError
    repo = SQLAlchemyArticleRepository(
        session_factory=AsyncMock(), analytics_session_factory=AsyncMock()
    )
    assert repo is not None


def test_list_articles_endpoint_as_admin_with_stock(mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims
    from backend.api.dependencies.services import get_article_catalog_orchestrator
    from backend.app.articles.orchestrator import ArticleCatalogOrchestrator

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@example.com",
        "role": "administrador",
        "tenant_id": 1,
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
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

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
        "tenant_id": 1,
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
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

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


class _FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self.statements = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def execute(self, stmt):
        self.statements.append(stmt)
        return self._results.pop(0)


def _compiled_sql(stmt) -> str:
    return str(stmt.compile(compile_kwargs={"literal_binds": True}))


def test_list_families_endpoint(mock_search_service):
    from backend.api.dependencies.auth import get_current_user_claims
    from backend.app.articles.models import Familia

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": 1,
        "branch_id": 1,
    }
    mock_search_service.list_families.return_value = [
        Familia(id_familia="01", des_familia="Medicamentos"),
        Familia(id_familia="02", des_familia="Perfumería"),
    ]
    app.dependency_overrides[get_article_search_service] = lambda: mock_search_service

    response = TestClient(app).get("/api/v1/articles/families")

    assert response.status_code == 200
    assert response.json() == [
        {"id_familia": "01", "des_familia": "Medicamentos"},
        {"id_familia": "02", "des_familia": "Perfumería"},
    ]
    app.dependency_overrides.clear()


def test_list_articles_forwards_barcode_search(mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims
    from backend.api.dependencies.services import get_article_catalog_orchestrator
    from backend.app.articles.orchestrator import ArticleCatalogOrchestrator

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@example.com",
        "role": "auditor",
        "tenant_id": 1,
        "branch_id": 1,
    }
    mock_orchestrator = AsyncMock(spec=ArticleCatalogOrchestrator)
    mock_orchestrator.get_enriched_catalog.return_value = (
        [
            Articulo(
                id_articulo="ART-00001",
                des_articulo="Amoxicilina 500mg",
                id_marca=1,
                pcio_com_siva=Decimal("10.00"),
            )
        ],
        1,
    )
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

    response = TestClient(app).get("/api/v1/articles?search=7791234567890")

    assert response.status_code == 200
    assert response.json()["items"][0]["id_articulo"] == "ART-00001"
    call = mock_orchestrator.get_enriched_catalog.call_args
    assert call.kwargs["search"] == "7791234567890"
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_repository_list_articles_search_matches_barcode():
    from unittest.mock import MagicMock

    from backend.adapters.repositories.article_repository import (
        SQLAlchemyArticleRepository,
    )

    count_result = MagicMock()
    count_result.scalar.return_value = 0
    items_result = MagicMock()
    items_result.scalars.return_value.unique.return_value.all.return_value = []
    session = _FakeSession([count_result, items_result])
    repo = SQLAlchemyArticleRepository(
        session_factory=lambda: session, analytics_session_factory=AsyncMock()
    )

    await repo.list_articles(search="7791234567890")

    for stmt in session.statements:
        sql = _compiled_sql(stmt)
        assert "codigos_barra_articulo.cod_barra = '7791234567890'" in sql
        assert "des_articulo" in sql


@pytest.mark.asyncio
async def test_repository_list_families_maps_rows():
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from backend.adapters.repositories.article_repository import (
        SQLAlchemyArticleRepository,
    )

    result = MagicMock()
    result.scalars.return_value.all.return_value = [
        SimpleNamespace(id_familia="01", des_familia="Medicamentos "),
        SimpleNamespace(id_familia="02", des_familia="Perfumería"),
    ]
    session = _FakeSession([result])
    repo = SQLAlchemyArticleRepository(
        session_factory=lambda: session, analytics_session_factory=AsyncMock()
    )

    families = await repo.list_families()

    assert [(f.id_familia, f.des_familia) for f in families] == [
        ("01", "Medicamentos"),
        ("02", "Perfumería"),
    ]
    assert "ORDER BY familias.id_familia" in _compiled_sql(session.statements[0])


def test_list_articles_serializes_audited_by_for_supervisor(
    mock_orchestrator, mock_work_session_service
):
    from backend.api.dependencies.auth import get_current_user_claims

    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "supervisor@example.com",
        "role": "supervisor",
        "tenant_id": 1,
        "branch_id": 1,
    }
    audited = _audited_article().model_copy(update={"audited_by": "Carlos Auditor"})
    unaudited = _audited_article().model_copy(
        update={"id_articulo": "ART-002", "fue_auditado": False}
    )
    mock_orchestrator.get_enriched_catalog.return_value = ([audited, unaudited], 2)
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )

    response = TestClient(app).get("/api/v1/articles")

    assert response.status_code == 200
    first, second = response.json()["items"]
    assert first["audited_by"] == "Carlos Auditor"
    assert first["fue_auditado"] is True
    assert "pcio_com_siva" not in first
    assert second["audited_by"] is None
    assert second["fue_auditado"] is False
    assert mock_orchestrator.get_enriched_catalog.await_args.kwargs["tenant_id"] == 1

    app.dependency_overrides.clear()


def test_search_and_get_article_forward_tenant_id(
    mock_orchestrator, mock_work_session_service
):
    _override_search_deps("auditor", mock_orchestrator, mock_work_session_service)
    mock_orchestrator.search_and_enrich_articles.return_value = []
    mock_orchestrator.get_enriched_article.return_value = _audited_article()
    client = TestClient(app)

    assert client.get("/api/v1/articles/search?query=x").status_code == 200
    assert client.get("/api/v1/articles/ART-00002").status_code == 200

    search_kwargs = mock_orchestrator.search_and_enrich_articles.await_args.kwargs
    assert search_kwargs["tenant_id"] == 1
    assert mock_orchestrator.get_enriched_article.await_args.kwargs["tenant_id"] == 1

    app.dependency_overrides.clear()


def _override_list_deps(claims, mock_orchestrator, mock_work_session_service):
    from backend.api.dependencies.auth import get_current_user_claims

    app.dependency_overrides[get_current_user_claims] = lambda: claims
    mock_orchestrator.get_enriched_catalog.return_value = ([], 0)
    app.dependency_overrides[get_article_catalog_orchestrator] = lambda: (
        mock_orchestrator
    )
    app.dependency_overrides[get_work_session_service] = lambda: (
        mock_work_session_service
    )


@pytest.mark.parametrize("tenant_claim", [None, "tenant-01", "", "abc"])
def test_list_articles_rejects_malformed_tenant_claim(
    tenant_claim, mock_orchestrator, mock_work_session_service
):
    claims = {"sub": "a@example.com", "role": "auditor", "tenant_id": tenant_claim}
    _override_list_deps(claims, mock_orchestrator, mock_work_session_service)

    response = TestClient(app).get("/api/v1/articles")

    assert response.status_code == 401
    mock_orchestrator.get_enriched_catalog.assert_not_called()

    app.dependency_overrides.clear()


@pytest.mark.parametrize("tenant_claim,expected", [("2", 2), (3, 3)])
def test_list_articles_accepts_numeric_tenant_claim(
    tenant_claim, expected, mock_orchestrator, mock_work_session_service
):
    claims = {"sub": "a@example.com", "role": "auditor", "tenant_id": tenant_claim}
    _override_list_deps(claims, mock_orchestrator, mock_work_session_service)

    response = TestClient(app).get("/api/v1/articles")

    assert response.status_code == 200
    kwargs = mock_orchestrator.get_enriched_catalog.await_args.kwargs
    assert kwargs["tenant_id"] == expected

    app.dependency_overrides.clear()


def test_list_articles_missing_tenant_claim_defaults_to_one(
    mock_orchestrator, mock_work_session_service
):
    claims = {"sub": "a@example.com", "role": "auditor"}
    _override_list_deps(claims, mock_orchestrator, mock_work_session_service)

    response = TestClient(app).get("/api/v1/articles")

    assert response.status_code == 200
    assert mock_orchestrator.get_enriched_catalog.await_args.kwargs["tenant_id"] == 1

    app.dependency_overrides.clear()


def test_article_catalog_orchestrator_dependency_wires_user_repository():
    from backend.adapters.repositories.user_repository import SQLAlchemyUserRepository

    orchestrator = get_article_catalog_orchestrator(
        search_service=AsyncMock(spec=ArticleSearchService),
        stock_lookup_service=AsyncMock(),
    )

    assert isinstance(orchestrator, ArticleCatalogOrchestrator)
    assert isinstance(orchestrator.user_repository, SQLAlchemyUserRepository)
