from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.articles.models import Articulo

class ArticleRepositoryPort(ABC):
    """
    Abstract port for accessing article data from the repository layer.
    Pure domain interface, decoupled from database ORMs.
    """
    @abstractmethod
    async def get_by_id(self, id_articulo: str) -> Optional[Articulo]:
        """
        Retrieve an article by its unique Article ID.
        """
        pass

    @abstractmethod
    async def get_by_barcode(self, barcode: str) -> Optional[Articulo]:
        """
        Retrieve an article by its exact barcode string.
        """
        pass

    @abstractmethod
    async def search(self, query: str) -> List[Articulo]:
        """
        Multi-field search supporting exact match by Article ID,
        exact match by numeric barcode, or partial match by description.
        """
        pass
