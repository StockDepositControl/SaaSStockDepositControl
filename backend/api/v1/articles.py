import math
from typing import List, Union, Any, Optional
from fastapi import APIRouter, Depends, Query, Path

from backend.app.articles.models import ArticuloPublicOut, ArticuloAdminOut
from backend.app.articles.services import ArticleSearchService
from backend.app.work_sessions.services import WorkSessionService
from backend.api.dependencies.auth import get_current_user_claims
from backend.api.dependencies.services import get_article_search_service, get_work_session_service

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
    work_session_service: WorkSessionService = Depends(get_work_session_service)
) -> List[Any]:
    """
    Search articles catalog.
    """
    tenant_id = claims.get("tenant_id")
    branch_id = claims.get("branch_id", 1)
    
    session = await work_session_service.get_or_create_active_session(tenant_id=tenant_id, branch_id=branch_id)
    results = await search_service.search_articles(query, active_session_id=session.session_id)

    user_role = claims.get("role", "").lower()
    is_admin = (user_role == "administrador")

    if is_admin:
        return [ArticuloAdminOut.model_validate(art) for art in results]
    else:
        return [ArticuloPublicOut.model_validate(art) for art in results]


@router.get(
    "/all",
    response_model=List[Union[ArticuloAdminOut, ArticuloPublicOut]],
    summary="Get all articles without pagination",
    description="Retrieves the entire catalog of articles. Dynamically masks financial data based on user role."
)
async def get_all_articles(
    claims: dict = Depends(get_current_user_claims),
    search_service: ArticleSearchService = Depends(get_article_search_service),
) -> List[Any]:
    """
    Retrieve all articles in the catalog without pagination.
    """
    articles = await search_service.list_all_articles()

    user_role = claims.get("role", "").lower()
    is_admin = (user_role == "administrador")

    if is_admin:
        return [ArticuloAdminOut.model_validate(art) for art in articles]
    else:
        return [ArticuloPublicOut.model_validate(art) for art in articles]


@router.get(
    "",
    summary="List and filter articles with pagination",
    description="Retrieves a paginated list of articles, optionally filtered by family, group, or search term."
)
async def list_articles(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term filter"),
    id_familia: Optional[str] = Query(None, description="Family ID filter"),
    id_grupo: Optional[str] = Query(None, description="Group ID filter"),
    fue_auditado: Optional[bool] = Query(None, description="Filter by audited status"),
    claims: dict = Depends(get_current_user_claims),
    search_service: ArticleSearchService = Depends(get_article_search_service),
    work_session_service: WorkSessionService = Depends(get_work_session_service),
) -> dict:
    tenant_id = claims.get("tenant_id")
    branch_id = claims.get("branch_id", 1)

    session = await work_session_service.get_or_create_active_session(tenant_id=tenant_id, branch_id=branch_id)
    items, total = await search_service.list_articles(
        page=page,
        limit=limit,
        search=search,
        id_familia=id_familia,
        id_grupo=id_grupo,
        fue_auditado=fue_auditado,
        active_session_id=session.session_id,
    )

    user_role = claims.get("role", "").lower()
    is_admin = (user_role == "administrador")

    if is_admin:
        mapped_items = [ArticuloAdminOut.model_validate(art).model_dump() for art in items]
    else:
        mapped_items = [ArticuloPublicOut.model_validate(art).model_dump() for art in items]

    pages = math.ceil(total / limit) if limit else 0

    return {
        "items": mapped_items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


@router.get(
    "/{id_articulo}",
    response_model=Union[ArticuloAdminOut, ArticuloPublicOut],
    summary="Get a single article by ID"
)
async def get_article(
    id_articulo: str = Path(..., description="Article code"),
    claims: dict = Depends(get_current_user_claims),
    search_service: ArticleSearchService = Depends(get_article_search_service),
    work_session_service: WorkSessionService = Depends(get_work_session_service)
) -> Any:
    tenant_id = claims.get("tenant_id")
    branch_id = claims.get("branch_id", 1)
    
    session = await work_session_service.get_or_create_active_session(tenant_id=tenant_id, branch_id=branch_id)
    article = await search_service.get_article_by_id(id_articulo, active_session_id=session.session_id)

    user_role = claims.get("role", "").lower()
    is_admin = (user_role == "administrador")

    if is_admin:
        return ArticuloAdminOut.model_validate(article)
    else:
        return ArticuloPublicOut.model_validate(article)
