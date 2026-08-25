from typing import List, Optional, Tuple
from backend.app.articles.models import Articulo
from backend.app.articles.ports import ArticleRepositoryPort
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException

class ArticleSearchService:
    """
    Domain service for searching and retrieving article catalog entries.
    Implements business logic around article lookup and validation.
    """
    def __init__(self, article_repository: ArticleRepositoryPort):
        self.article_repository = article_repository

    async def search_articles(self, query: str, active_session_id: Optional[int] = None) -> List[Articulo]:
        """
        Executes multi-field search across article ID, barcode, or description.
        Returns a list of matching Articulo domain entities.
        """
        clean_query = query.strip() if query else ""
        if not clean_query:
            return []

        results = await self.article_repository.search(clean_query, active_session_id=active_session_id)
        return results

    async def get_article_by_id(self, id_articulo: str, active_session_id: Optional[int] = None) -> Articulo:
        """
        Retrieves a specific article by ID or raises EntityNotFoundException.
        """
        article = await self.article_repository.get_by_id(id_articulo, active_session_id=active_session_id)
        if not article:
            raise EntityNotFoundException(f"Article '{id_articulo}' not found.")
        return article

    async def list_articles(
        self,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        id_familia: Optional[str] = None,
        id_grupo: Optional[str] = None,
        fue_auditado: Optional[bool] = None,
        active_session_id: Optional[int] = None
    ) -> Tuple[List[Articulo], int]:
        """
        Retrieves a paginated list of articles.
        """
        if page < 1:
            page = 1
        if limit < 1:
            limit = 50
        if limit > 200:
            limit = 200

        return await self.article_repository.list_articles(
            page=page,
            limit=limit,
            search=search,
            id_familia=id_familia,
            id_grupo=id_grupo,
            fue_auditado=fue_auditado,
            active_session_id=active_session_id
        )

    async def list_all_articles(self) -> List[Articulo]:
        """
        Retrieves the full catalog of articles without pagination.
        """
        items, _ = await self.article_repository.list_articles(
            page=1,
            limit=10000,
            active_session_id=None
        )
        return items
