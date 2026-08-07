import pytest
from unittest.mock import AsyncMock
from decimal import Decimal

from backend.app.articles.models import Articulo
from backend.app.articles.ports import ArticleRepositoryPort
from backend.app.articles.services import ArticleSearchService
from backend.app.exceptions import EntityNotFoundException

@pytest.fixture
def mock_article_repo():
    return AsyncMock(spec=ArticleRepositoryPort)

@pytest.fixture
def sample_article():
    return Articulo(
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

@pytest.mark.asyncio
async def test_search_articles_empty_query(mock_article_repo):
    service = ArticleSearchService(article_repository=mock_article_repo)

    result = await service.search_articles("   ")
    assert result == []
    mock_article_repo.search.assert_not_called()

@pytest.mark.asyncio
async def test_search_articles_success(mock_article_repo, sample_article):
    mock_article_repo.search.return_value = [sample_article]
    service = ArticleSearchService(article_repository=mock_article_repo)

    results = await service.search_articles("Ibuprofeno")

    assert len(results) == 1
    assert results[0].id_articulo == "1042"
    assert results[0].des_articulo == "Ibuprofeno 400mg"
    mock_article_repo.search.assert_called_once_with("Ibuprofeno")

@pytest.mark.asyncio
async def test_get_article_by_id_success(mock_article_repo, sample_article):
    mock_article_repo.get_by_id.return_value = sample_article
    service = ArticleSearchService(article_repository=mock_article_repo)

    result = await service.get_article_by_id("1042")

    assert result.id_articulo == "1042"
    mock_article_repo.get_by_id.assert_called_once_with("1042")

@pytest.mark.asyncio
async def test_get_article_by_id_not_found(mock_article_repo):
    mock_article_repo.get_by_id.return_value = None
    service = ArticleSearchService(article_repository=mock_article_repo)

    with pytest.raises(EntityNotFoundException) as exc_info:
        await service.get_article_by_id("NONEXISTENT")

    assert "NONEXISTENT" in str(exc_info.value)
