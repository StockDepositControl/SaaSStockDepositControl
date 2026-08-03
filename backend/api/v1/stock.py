from fastapi import APIRouter, Depends, Query, status
from typing import Union
from backend.app.movements.models import (
    AuditEntryInput,
    AuditEntryResult,
    AuditBatchInput,
    AuditBatchResult,
    ArticleStockPositionPublicOut,
    ArticleStockPositionAdminOut,
)
from backend.app.movements.services import AuditService
from backend.app.articles.services import ArticleSearchService
from backend.api.dependencies.auth import get_current_user_claims, RoleChecker
from backend.api.dependencies.services import get_audit_service, get_article_search_service


router = APIRouter()

# Enforce RBAC for audit registration endpoints
require_audit_roles = RoleChecker(allowed_roles=["administrador", "supervisor", "auditor"])

@router.post(
    "/audit",
    response_model=AuditEntryResult,
    status_code=status.HTTP_201_CREATED,
    summary="Register single stock audit entry",
    description="Registers physical stock audit count, computes theoretical discrepancy (delta), voucher classification, and valorized cost.",
)
async def register_single_audit(
    entry: AuditEntryInput,
    claims: dict = Depends(require_audit_roles),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditEntryResult:
    tenant_id = str(claims.get("tenant_id", "1"))
    id_usuario = int(claims.get("id_usuario", 1))

    result = await audit_service.register_single_audit(
        tenant_id=tenant_id,
        id_usuario=id_usuario,
        entry=entry,
    )
    return result


@router.post(
    "/audit/batch",
    response_model=AuditBatchResult,
    status_code=status.HTTP_200_OK,
    summary="Register batch stock audit entries (offline sync)",
    description="Processes queued audit records transmitted during mobile offline reconnection worker flush.",
)
async def register_batch_audit(
    batch: AuditBatchInput,
    claims: dict = Depends(require_audit_roles),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditBatchResult:
    tenant_id = str(claims.get("tenant_id", "1"))
    id_usuario = int(claims.get("id_usuario", 1))

    result = await audit_service.register_batch_audit(
        tenant_id=tenant_id,
        id_usuario=id_usuario,
        batch=batch,
    )
    return result

@router.get(
    "/position",
    response_model=Union[ArticleStockPositionAdminOut, ArticleStockPositionPublicOut],
    status_code=status.HTTP_200_OK,
    summary="Fetch Article Stock Position",
    description="Retrieves article catalog metadata alongside its current theoretical stock scoped to a specific deposit.",
)
async def get_article_stock_position(
    id_articulo: str = Query(..., description="Article Identifier"),
    id_sucursal: int = Query(..., description="Branch/Store ID"),
    id_deposito: int = Query(..., description="Warehouse/Deposit ID"),
    claims: dict = Depends(require_audit_roles),
    search_service: ArticleSearchService = Depends(get_article_search_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> Union[ArticleStockPositionAdminOut, ArticleStockPositionPublicOut]:
    tenant_id = str(claims.get("tenant_id", "1"))
    user_role = claims.get("role", "").lower()
    is_admin = (user_role == "administrador")

    # 1. Fetch Article Metadata
    article = await search_service.get_article_by_id(id_articulo)

    # 2. Fetch Stock Position
    stock_pos = await audit_service.stock_repository.get_stock_position(
        tenant_id=tenant_id,
        id_sucursal=id_sucursal,
        id_deposito=id_deposito,
        id_articulo=id_articulo,
    )

    # 3. Combine Data
    stock_teorico = stock_pos.stock_teorico if stock_pos else 0

    base_data = {
        "id_articulo": article.id_articulo,
        "des_articulo": article.des_articulo,
        "presentacion": article.presentacion,
        "id_marca": article.id_marca,
        "des_marca": article.des_marca,
        "id_familia": article.id_familia,
        "des_familia": article.des_familia,
        "id_grupo": article.id_grupo,
        "des_grupo": article.des_grupo,
        "id_sucursal": id_sucursal,
        "id_deposito": id_deposito,
        "stock_teorico": stock_teorico,
    }

    if is_admin:
        base_data["pcio_com_siva"] = article.pcio_com_siva
        return ArticleStockPositionAdminOut(**base_data)
    else:
        return ArticleStockPositionPublicOut(**base_data)

