from typing import Optional, Union

from backend.api.dependencies.auth import RoleChecker
from backend.api.dependencies.services import (
    get_article_search_service,
    get_audit_service,
    get_stock_kpi_service,
    get_work_session_service,
)
from backend.api.v1.schemas.stock import (
    ArticleStockPositionAdminOut,
    ArticleStockPositionPublicOut,
)
from backend.app.articles.services import ArticleSearchService
from backend.app.movements.schemas import (
    AuditBatchInput,
    AuditBatchResult,
    AuditEntryRequest,
    AuditEntryResult,
    DashboardKPIsPublicOut,
    DashboardKPIsResponse,
)
from backend.app.movements.services import AuditService, StockKPIService
from backend.app.work_sessions.services import WorkSessionService
from fastapi import APIRouter, Depends, Query, status

router = APIRouter()

# Read access (stock position, dashboard KPIs) is open to every role
require_audit_roles = RoleChecker(
    allowed_roles=["administrador", "supervisor", "auditor"]
)

# Registering audits is a field operation: administrators are excluded
require_audit_writer_roles = RoleChecker(allowed_roles=["supervisor", "auditor"])


@router.post(
    "/audit",
    response_model=AuditEntryResult,
    status_code=status.HTTP_201_CREATED,
    summary="Register single stock audit entry",
    description=(
        "Registers physical stock audit count or variance, computes theoretical "
        "discrepancy (delta), voucher classification, and valorized cost."
    ),
)
async def register_single_audit(
    entry: AuditEntryRequest,
    claims: dict = Depends(require_audit_writer_roles),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditEntryResult:
    tenant_id = str(claims.get("tenant_id", "1"))
    id_usuario = int(claims.get("id_usuario") or claims.get("user_id", 1))

    # Defensive fallback normalization
    updates = {}
    if entry.id_sucursal is None:
        updates["id_sucursal"] = claims.get("branch_id") or 1
    if entry.id_deposito is None:
        updates["id_deposito"] = 1

    effective_entry = entry.model_copy(update=updates) if updates else entry

    result = await audit_service.register_single_audit(
        tenant_id=tenant_id,
        id_usuario=id_usuario,
        entry=effective_entry,
    )
    return result


@router.get(
    "/position",
    response_model=Union[ArticleStockPositionAdminOut, ArticleStockPositionPublicOut],
    status_code=status.HTTP_200_OK,
    summary="Fetch Article Stock Position",
    description=(
        "Retrieves article catalog metadata alongside its current stock position "
        "scoped to a specific deposit."
    ),
)
async def get_article_stock_position(
    id_articulo: str = Query(..., description="Article Identifier"),
    id_sucursal: Optional[int] = Query(None, description="Branch/Store ID"),
    id_deposito: Optional[int] = Query(None, description="Warehouse/Deposit ID"),
    claims: dict = Depends(require_audit_roles),
    search_service: ArticleSearchService = Depends(get_article_search_service),
    audit_service: AuditService = Depends(get_audit_service),
) -> Union[ArticleStockPositionAdminOut, ArticleStockPositionPublicOut]:
    branch_id = claims.get("branch_id")
    user_role = claims.get("role", "").lower()
    is_admin = user_role == "administrador"

    resolved_sucursal = (
        id_sucursal
        if id_sucursal is not None
        else (branch_id if branch_id is not None else 1)
    )
    resolved_deposito = id_deposito if id_deposito is not None else 1

    # 1. Fetch Article Metadata
    article = await search_service.get_article_by_id(id_articulo)

    try:
        tenant_id_int = int(claims.get("tenant_id", 1))
    except (ValueError, TypeError):
        tenant_id_int = 1

    # 2. Fetch Stock Position using fallback logic
    stock_pos = await audit_service.stock_lookup_service.get_effective_stock(
        tenant_id=tenant_id_int,
        id_sucursal=resolved_sucursal,
        id_deposito=resolved_deposito,
        id_articulo=id_articulo,
    )

    # 3. Combine Data
    stock_real = stock_pos.stock_real if stock_pos else 0

    base_data = {
        "des_articulo": article.des_articulo,
        "presentacion": article.presentacion,
        "des_marca": article.des_marca,
        "des_familia": article.des_familia,
        "des_grupo": article.des_grupo,
        "id_sucursal": resolved_sucursal,
        "id_deposito": resolved_deposito,
        "stock_real": stock_real,
    }

    if is_admin:
        base_data["pcio_com_siva"] = article.pcio_com_siva
        return ArticleStockPositionAdminOut(**base_data)
    else:
        return ArticleStockPositionPublicOut(**base_data)


@router.post(
    "/audit/batch",
    response_model=AuditBatchResult,
    status_code=status.HTTP_200_OK,
    summary="Register batch stock audit entries (offline sync)",
    description=(
        "Processes queued audit records transmitted during mobile offline "
        "reconnection worker flush."
    ),
)
async def register_batch_audit(
    batch: AuditBatchInput,
    claims: dict = Depends(require_audit_writer_roles),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditBatchResult:
    tenant_id = str(claims.get("tenant_id", "1"))
    id_usuario = int(claims.get("user_id") or claims.get("id_usuario", 1))

    default_branch = claims.get("branch_id") or 1
    normalized_items = []
    for item in batch.items:
        updates = {}
        if item.id_sucursal is None:
            updates["id_sucursal"] = default_branch
        if item.id_deposito is None:
            updates["id_deposito"] = 1
        normalized_items.append(item.model_copy(update=updates) if updates else item)

    effective_batch = AuditBatchInput(items=normalized_items)

    result = await audit_service.register_batch_audit(
        tenant_id=tenant_id,
        id_usuario=id_usuario,
        batch=effective_batch,
    )
    return result


@router.get(
    "/kpis",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Get aggregated stock and audit KPIs for dashboard",
    description=(
        "Returns database-aggregated dashboard KPIs for the active work session. "
        "Valorized amounts are included only for administrators."
    ),
    responses={200: {"model": Union[DashboardKPIsResponse, DashboardKPIsPublicOut]}},
)
async def get_dashboard_kpis(
    id_deposito: int = Query(1, ge=1, description="Warehouse ID"),
    claims: dict = Depends(require_audit_roles),
    service: StockKPIService = Depends(get_stock_kpi_service),
    work_session_service: WorkSessionService = Depends(get_work_session_service),
) -> Union[DashboardKPIsResponse, DashboardKPIsPublicOut]:
    tenant_id = str(claims.get("tenant_id", "1"))
    branch_id = claims.get("branch_id") or 1
    session = await work_session_service.get_or_create_active_session(
        tenant_id=tenant_id, branch_id=branch_id
    )
    is_admin = claims.get("role", "").lower() == "administrador"

    return await service.get_dashboard_kpis(
        tenant_id=tenant_id,
        branch_id=branch_id,
        deposit_id=id_deposito,
        session_id=session.session_id,
        is_admin=is_admin,
    )
