from typing import List, Optional, Tuple, Dict
from backend.app.articles.models import Articulo
from backend.app.articles.services import ArticleSearchService
from backend.app.movements.services import StockLookupService

class ArticleCatalogOrchestrator:
    """
    Pure Fabrication domain application service that orchestrates article catalog retrieval
    with batch stock enrichment across bounded contexts.
    """
    def __init__(
        self,
        article_search_service: ArticleSearchService,
        stock_lookup_service: StockLookupService,
    ):
        self.article_search_service = article_search_service
        self.stock_lookup_service = stock_lookup_service

    async def get_enriched_catalog(
        self,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        id_familia: Optional[str] = None,
        id_grupo: Optional[str] = None,
        fue_auditado: Optional[bool] = None,
        deposit_id: int = 1,
        active_session_id: Optional[int] = None,
    ) -> Tuple[List[Articulo], int]:
        """
        Orchestrates:
        1. Retrieval of paginated articles catalog via ArticleSearchService.
        2. Batch lookup of effective stock levels (audit priority with stock fallback) via StockLookupService.
        3. Enrichment of article entities with resolved stock_real without mutating original instances.
        Returns a tuple of (enriched_articles, total_count).
        """
        articles, total = await self.article_search_service.list_articles(
            page=page,
            limit=limit,
            search=search,
            id_familia=id_familia,
            id_grupo=id_grupo,
            fue_auditado=fue_auditado,
            active_session_id=active_session_id,
        )

        if not articles:
            return [], total

        article_ids = [art.id_articulo for art in articles]

        stock_map = await self.stock_lookup_service.get_effective_stocks_batch(
            article_ids=article_ids,
            deposit_id=deposit_id,
            active_session_id=active_session_id,
        )

        enriched_articles = [
            art.model_copy(update={"stock_real": stock_map.get(art.id_articulo, 0)})
            for art in articles
        ]

        return enriched_articles, total

    async def get_enriched_article(
        self,
        id_articulo: str,
        deposit_id: int = 1,
        active_session_id: Optional[int] = None,
    ) -> Articulo:
        """
        Orchestrates:
        1. Retrieval of single article entity via ArticleSearchService (raises EntityNotFoundException if not found).
        2. Lookup of effective stock level via StockLookupService.get_effective_stocks_batch.
        3. Enrichment of article entity with resolved stock_real without mutating original instance.
        Returns the enriched Articulo domain entity.
        """
        article = await self.article_search_service.get_article_by_id(
            id_articulo=id_articulo,
            active_session_id=active_session_id,
        )

        stock_map = await self.stock_lookup_service.get_effective_stocks_batch(
            article_ids=[id_articulo],
            deposit_id=deposit_id,
            active_session_id=active_session_id,
        )

        return article.model_copy(
            update={"stock_real": stock_map.get(id_articulo, 0)}
        )

