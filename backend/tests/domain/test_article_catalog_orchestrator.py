import pytest
from unittest.mock import AsyncMock
from decimal import Decimal

from backend.app.articles.models import Articulo
from backend.app.articles.services import ArticleSearchService
from backend.app.articles.orchestrator import ArticleCatalogOrchestrator
from backend.app.movements.services import StockLookupService


@pytest.fixture
def mock_search_service():
    return AsyncMock(spec=ArticleSearchService)


@pytest.fixture
def mock_stock_lookup_service():
    return AsyncMock(spec=StockLookupService)


@pytest.fixture
def orchestrator(mock_search_service, mock_stock_lookup_service):
    return ArticleCatalogOrchestrator(
        article_search_service=mock_search_service,
        stock_lookup_service=mock_stock_lookup_service,
    )


@pytest.fixture
def sample_articles():
    return [
        Articulo(
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
        ),
        Articulo(
            id_articulo="1043",
            presentacion="Caja x 10",
            des_articulo="Paracetamol 500mg",
            id_marca=2,
            des_marca="Genfar",
            id_familia="01",
            des_familia="Medicamentos",
            id_grupo="02",
            des_grupo="Analgésicos",
            pcio_com_siva=Decimal("80.00"),
            fue_auditado=True,
        ),
    ]


@pytest.mark.asyncio
async def test_orchestrator_enriches_articles_with_stock(
    orchestrator, mock_search_service, mock_stock_lookup_service, sample_articles
):
    mock_search_service.list_articles.return_value = (sample_articles, 2)
    mock_stock_lookup_service.get_effective_stocks_batch.return_value = {
        "1042": 15,
        "1043": 30,
    }

    articles, total = await orchestrator.get_enriched_catalog(
        page=1,
        limit=50,
        deposit_id=1,
        active_session_id=5,
    )

    assert total == 2
    assert len(articles) == 2

    # Check enrichment
    assert articles[0].id_articulo == "1042"
    assert articles[0].stock_real == 15

    assert articles[1].id_articulo == "1043"
    assert articles[1].stock_real == 30

    mock_search_service.list_articles.assert_called_once_with(
        page=1,
        limit=50,
        search=None,
        id_familia=None,
        id_grupo=None,
        fue_auditado=None,
        active_session_id=5,
    )
    mock_stock_lookup_service.get_effective_stocks_batch.assert_called_once_with(
        article_ids=["1042", "1043"],
        deposit_id=1,
        active_session_id=5,
    )


@pytest.mark.asyncio
async def test_orchestrator_empty_page(orchestrator, mock_search_service, mock_stock_lookup_service):
    mock_search_service.list_articles.return_value = ([], 0)

    articles, total = await orchestrator.get_enriched_catalog(page=1, limit=50, deposit_id=1)

    assert articles == []
    assert total == 0
    mock_stock_lookup_service.get_effective_stocks_batch.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_missing_stock_defaults_to_zero(
    orchestrator, mock_search_service, mock_stock_lookup_service, sample_articles
):
    mock_search_service.list_articles.return_value = (sample_articles, 2)
    # Only "1042" has stock; "1043" is absent
    mock_stock_lookup_service.get_effective_stocks_batch.return_value = {"1042": 15}

    articles, total = await orchestrator.get_enriched_catalog(deposit_id=2)

    assert articles[0].stock_real == 15
    assert articles[1].stock_real == 0
