from typing import Dict, List, Optional, Tuple

from backend.app.articles.models import Articulo
from backend.app.articles.services import ArticleSearchService
from backend.app.movements.services import StockLookupService
from backend.app.users.ports import UserRepositoryPort


class ArticleCatalogOrchestrator:
    """
    Pure Fabrication domain application service that orchestrates article catalog
    retrieval
    with batch stock and auditor-name enrichment across bounded contexts.
    """

    def __init__(
        self,
        article_search_service: ArticleSearchService,
        stock_lookup_service: StockLookupService,
        user_repository: Optional[UserRepositoryPort] = None,
    ):
        self.article_search_service = article_search_service
        self.stock_lookup_service = stock_lookup_service
        self.user_repository = user_repository

    async def _resolve_auditor_names(
        self,
        article_ids: List[str],
        active_session_id: Optional[int],
        tenant_id: Optional[int],
    ) -> Dict[str, str]:
        """
        Resolves {article_code: auditor display name} for the latest audit of each
        article in the active session. Users are loaded once per call via
        list_by_tenant; unresolvable user IDs are omitted.
        """
        if (
            self.user_repository is None
            or active_session_id is None
            or tenant_id is None
            or not article_ids
        ):
            return {}

        auditor_ids = await self.stock_lookup_service.get_session_auditors_batch(
            session_id=active_session_id, article_ids=article_ids
        )
        if not auditor_ids:
            return {}

        users = await self.user_repository.list_by_tenant(tenant_id)
        user_names = {u.user_id: f"{u.first_name} {u.last_name}".strip() for u in users}
        return {
            code: user_names[user_id]
            for code, user_id in auditor_ids.items()
            if user_id in user_names
        }

    @staticmethod
    def _enrich(
        article: Articulo, stock_map: Dict[str, int], auditor_names: Dict[str, str]
    ) -> Articulo:
        return article.model_copy(
            update={
                "stock_real": stock_map.get(article.id_articulo, 0),
                "audited_by": (
                    auditor_names.get(article.id_articulo)
                    if article.fue_auditado
                    else None
                ),
            }
        )

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
        tenant_id: Optional[int] = None,
    ) -> Tuple[List[Articulo], int]:
        """
        Orchestrates:
        1. Retrieval of paginated articles catalog via ArticleSearchService.
        2. Batch lookup of effective stock levels (audit priority with stock fallback)
           via StockLookupService.
        3. Resolution of the latest auditor's name per article (when a session and
           tenant are given).
        4. Enrichment of article entities with resolved stock_real and audited_by
           without mutating original instances.
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

        auditor_names = await self._resolve_auditor_names(
            article_ids, active_session_id, tenant_id
        )

        enriched_articles = [
            self._enrich(art, stock_map, auditor_names) for art in articles
        ]

        return enriched_articles, total

    async def get_enriched_article(
        self,
        id_articulo: str,
        deposit_id: int = 1,
        active_session_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
    ) -> Articulo:
        """
        Orchestrates:
        1. Retrieval of single article entity via ArticleSearchService (raises
           EntityNotFoundException if not found).
        2. Lookup of effective stock level via
           StockLookupService.get_effective_stocks_batch.
        3. Enrichment of article entity with resolved stock_real and audited_by
           without mutating original instance.
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

        auditor_names = await self._resolve_auditor_names(
            [id_articulo], active_session_id, tenant_id
        )

        return self._enrich(article, stock_map, auditor_names)

    async def search_and_enrich_articles(
        self,
        query: str,
        deposit_id: int = 1,
        active_session_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
    ) -> List[Articulo]:
        """
        Orchestrates:
        1. Multi-field article search via ArticleSearchService.
        2. Batch lookup of effective stock levels via StockLookupService
           (skipped when the search yields no matches).
        3. Enrichment of article entities with resolved stock_real and audited_by
           without mutating original instances.
        Returns the list of enriched Articulo domain entities.
        """
        articles = await self.article_search_service.search_articles(
            query=query,
            active_session_id=active_session_id,
        )

        if not articles:
            return []

        article_ids = [art.id_articulo for art in articles]

        stock_map = await self.stock_lookup_service.get_effective_stocks_batch(
            article_ids=article_ids,
            deposit_id=deposit_id,
            active_session_id=active_session_id,
        )
        auditor_names = await self._resolve_auditor_names(
            article_ids, active_session_id, tenant_id
        )

        return [self._enrich(art, stock_map, auditor_names) for art in articles]
