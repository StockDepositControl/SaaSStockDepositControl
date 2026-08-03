from typing import List, Optional
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

    async def search_articles(self, query: str) -> List[Articulo]:
        """
        Executes multi-field search across article ID, barcode, or description.
        Returns a list of matching Articulo domain entities.
        """
        clean_query = query.strip() if query else ""
        if not clean_query:
            return []

        results = await self.article_repository.search(clean_query)
        return results

    async def get_article_by_id(self, id_articulo: str) -> Articulo:
        """
        Retrieves a specific article by ID or raises EntityNotFoundException.
        """
        article = await self.article_repository.get_by_id(id_articulo)
        if not article:
            raise EntityNotFoundException(f"Article '{id_articulo}' not found.")
        return article
