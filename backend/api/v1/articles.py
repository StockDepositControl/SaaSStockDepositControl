from typing import List, Union, Any
from fastapi import APIRouter, Depends, Query

from backend.app.articles.models import ArticuloPublicOut, ArticuloAdminOut
from backend.app.articles.services import ArticleSearchService
from backend.api.dependencies.auth import get_current_user_claims
from backend.api.dependencies.services import get_article_search_service

router = APIRouter()

@router.get(
    "/search",
    response_model=List[Union[ArticuloAdminOut, ArticuloPublicOut]],
    summary="Search articles by ID, barcode, or description",
    description="Supports exact lookup by Article ID or barcode, and tokenized description search. Dynamically masks financial data based on user role."
)
async def search_articles(
    query: str = Query(..., min_length=1, description="Search query string (Article ID, barcode, or name token)"),
    claims: dict = Depends(get_current_user_claims),
    search_service: ArticleSearchService = Depends(get_article_search_service),
) -> List[Any]:
    """
    Search articles catalog. Returns ArticuloAdminOut for 'administrador' role,
    and ArticuloPublicOut for all other roles (supervisor, auditor).
    """
    results = await search_service.search_articles(query)

    user_role = claims.get("role", "").lower()
    is_admin = (user_role == "administrador")

    if is_admin:
        return [ArticuloAdminOut.model_validate(art) for art in results]
    else:
        return [ArticuloPublicOut.model_validate(art) for art in results]
