from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from backend.app.articles.models import Articulo
from backend.app.articles.orchestrator import ArticleCatalogOrchestrator
from backend.app.articles.services import ArticleSearchService
from backend.app.exceptions import EntityNotFoundException
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
async def test_orchestrator_empty_page(
    orchestrator, mock_search_service, mock_stock_lookup_service
):
    mock_search_service.list_articles.return_value = ([], 0)

    articles, total = await orchestrator.get_enriched_catalog(
        page=1, limit=50, deposit_id=1
    )

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


@pytest.mark.asyncio
async def test_orchestrator_get_enriched_article_success(
    orchestrator, mock_search_service, mock_stock_lookup_service, sample_articles
):
    single_article = sample_articles[0]
    mock_search_service.get_article_by_id.return_value = single_article
    mock_stock_lookup_service.get_effective_stocks_batch.return_value = {"1042": 25}

    result = await orchestrator.get_enriched_article(
        id_articulo="1042",
        deposit_id=2,
        active_session_id=10,
    )

    assert result.id_articulo == "1042"
    assert result.stock_real == 25
    assert result.des_articulo == "Ibuprofeno 400mg"

    mock_search_service.get_article_by_id.assert_called_once_with(
        id_articulo="1042",
        active_session_id=10,
    )
    mock_stock_lookup_service.get_effective_stocks_batch.assert_called_once_with(
        article_ids=["1042"],
        deposit_id=2,
        active_session_id=10,
    )


@pytest.mark.asyncio
async def test_orchestrator_get_enriched_article_not_found(
    orchestrator, mock_search_service, mock_stock_lookup_service
):
    mock_search_service.get_article_by_id.side_effect = EntityNotFoundException(
        "Article '9999' not found."
    )

    with pytest.raises(EntityNotFoundException, match="Article '9999' not found."):
        await orchestrator.get_enriched_article(
            id_articulo="9999",
            deposit_id=1,
            active_session_id=5,
        )

    mock_search_service.get_article_by_id.assert_called_once_with(
        id_articulo="9999",
        active_session_id=5,
    )
    mock_stock_lookup_service.get_effective_stocks_batch.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_get_enriched_article_missing_stock_defaults_to_zero(
    orchestrator, mock_search_service, mock_stock_lookup_service, sample_articles
):
    single_article = sample_articles[0]
    mock_search_service.get_article_by_id.return_value = single_article
    mock_stock_lookup_service.get_effective_stocks_batch.return_value = {}

    result = await orchestrator.get_enriched_article(
        id_articulo="1042",
        deposit_id=1,
    )

    assert result.id_articulo == "1042"
    assert result.stock_real == 0


@pytest.mark.asyncio
async def test_search_and_enrich_articles_resolves_stock(
    orchestrator, mock_search_service, mock_stock_lookup_service, sample_articles
):
    mock_search_service.search_articles.return_value = sample_articles
    mock_stock_lookup_service.get_effective_stocks_batch.return_value = {
        "1042": 15,
        "1043": 30,
    }

    articles = await orchestrator.search_and_enrich_articles(
        "Ibu", deposit_id=1, active_session_id=10
    )

    assert [a.id_articulo for a in articles] == ["1042", "1043"]
    assert [a.stock_real for a in articles] == [15, 30]
    mock_search_service.search_articles.assert_awaited_once_with(
        query="Ibu", active_session_id=10
    )
    mock_stock_lookup_service.get_effective_stocks_batch.assert_called_once_with(
        article_ids=["1042", "1043"],
        deposit_id=1,
        active_session_id=10,
    )


@pytest.mark.asyncio
async def test_search_and_enrich_articles_empty_result(
    orchestrator, mock_search_service, mock_stock_lookup_service
):
    mock_search_service.search_articles.return_value = []

    articles = await orchestrator.search_and_enrich_articles(
        "zzz", deposit_id=1, active_session_id=None
    )

    assert articles == []
    mock_stock_lookup_service.get_effective_stocks_batch.assert_not_called()


@pytest.mark.asyncio
async def test_search_and_enrich_articles_audited_article_uses_session_count(
    orchestrator, mock_search_service, mock_stock_lookup_service
):
    audited = Articulo(
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
        fue_auditado=True,
    )
    mock_search_service.search_articles.return_value = [audited]
    # Session audit count (195) takes priority over baseline stock_posicion (194)
    mock_stock_lookup_service.get_effective_stocks_batch.return_value = {
        "ART-00002": 195
    }

    articles = await orchestrator.search_and_enrich_articles(
        "MED Esa", deposit_id=1, active_session_id=10
    )

    assert len(articles) == 1
    assert articles[0].stock_real == 195
    assert articles[0].fue_auditado is True
    mock_stock_lookup_service.get_effective_stocks_batch.assert_called_once_with(
        article_ids=["ART-00002"],
        deposit_id=1,
        active_session_id=10,
    )
