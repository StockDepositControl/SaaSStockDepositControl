from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from backend.app.articles.models import Articulo, Familia


class ArticleRepositoryPort(ABC):
    """
    Abstract port for accessing article data from the repository layer.
    Pure domain interface, decoupled from database ORMs.
    """

    @abstractmethod
    async def get_by_id(
        self, id_articulo: str, active_session_id: Optional[int] = None
    ) -> Optional[Articulo]:
        """
        Retrieve an article by its unique Article ID.
        """
        pass

    @abstractmethod
    async def get_by_barcode(
        self, barcode: str, active_session_id: Optional[int] = None
    ) -> Optional[Articulo]:
        """
        Retrieve an article by its exact barcode string.
        """
        pass

    @abstractmethod
    async def search(
        self, query: str, active_session_id: Optional[int] = None
    ) -> List[Articulo]:
        """
        Multi-field search supporting exact match by Article ID,
        exact match by numeric barcode, or partial match by description.
        """
        pass

    @abstractmethod
    async def list_articles(
        self,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        id_familia: Optional[str] = None,
        id_grupo: Optional[str] = None,
        fue_auditado: Optional[bool] = None,
        active_session_id: Optional[int] = None,
    ) -> Tuple[List[Articulo], int]:
        """
        Retrieves a paginated list of articles, optionally filtered.
        Calculates `fue_auditado` dynamically if `active_session_id` is provided.
        Returns a tuple of (items, total_count).
        """
        pass

    @abstractmethod
    async def get_barcode_by_article_id(self, id_articulo: str) -> Optional[str]:
        """
        Retrieve primary or first associated barcode string for a given article ID.
        """
        pass

    @abstractmethod
    async def list_families(self) -> List[Familia]:
        """
        Retrieve all product families ordered by family ID.
        """
        pass
