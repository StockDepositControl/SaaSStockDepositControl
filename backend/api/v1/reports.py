from datetime import date
from decimal import Decimal
from typing import Optional

from backend.api.dependencies.auth import RoleChecker
from backend.api.dependencies.services import (
    get_daily_inventory_balance_report_service,
    get_goods_received_report_service,
    get_shrinkage_report_service,
)
from backend.app.reports.schemas import (
    DailyInventoryBalanceFilters,
    DailyInventoryBalanceResponse,
    GoodsReceivedReportFilters,
    GoodsReceivedReportResponse,
    ShrinkageReportFilters,
    ShrinkageReportResponse,
)
from backend.app.reports.services import (
    DailyInventoryBalanceReportService,
    GoodsReceivedReportService,
    ShrinkageReportService,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status

router = APIRouter()

# Strictly enforce Role-Based Access Control: Administrators only
require_admin = RoleChecker(allowed_roles=["administrador"])


@router.get(
    "/shrinkage",
    response_model=ShrinkageReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Shrinkage and Financial Erosion Report",
    description="Retrieves consolidated shrinkage movements (audit removals/bajas), "
    "applies VAT fiscal classification (0% for medications, parameterized default for "
    "others), "
    "and calculates total financial erosion. Restricted to administrator role.",
)
async def get_shrinkage_report(
    start_date: date = Query(
        ..., description="Start date for audit records (inclusive)"
    ),
    end_date: date = Query(..., description="End date for audit records (inclusive)"),
    default_vat_rate: Decimal = Query(
        default=Decimal("0.21"),
        description="Default VAT rate applied to non-exempt product families",
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
    ),
    branch_id: Optional[int] = Query(
        default=None,
        description="Optional branch ID filter",
        ge=1,
    ),
    claims: dict = Depends(require_admin),
    service: ShrinkageReportService = Depends(get_shrinkage_report_service),
) -> ShrinkageReportResponse:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date",
        )

    tenant_id = str(claims.get("tenant_id", "1"))
    filters = ShrinkageReportFilters(
        start_date=start_date,
        end_date=end_date,
        default_vat_rate=default_vat_rate,
        branch_id=branch_id,
    )

    return await service.get_shrinkage_report(tenant_id=tenant_id, filters=filters)


@router.get(
    "/goods-received",
    response_model=GoodsReceivedReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Goods Received and Injected Capital Report",
    description=(
        "Retrieves consolidated goods received movements (audit additions/altas), "
        "applies VAT fiscal classification (0% for medications, parameterized "
        "default for others), "
        "and calculates total injected capital. Restricted to administrator role."
    ),
)
async def get_goods_received_report(
    start_date: date = Query(
        ..., description="Start date for audit records (inclusive)"
    ),
    end_date: date = Query(..., description="End date for audit records (inclusive)"),
    default_vat_rate: Decimal = Query(
        default=Decimal("0.21"),
        description="Default VAT rate applied to non-exempt product families",
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
    ),
    branch_id: Optional[int] = Query(
        default=None,
        description="Optional branch ID filter",
        ge=1,
    ),
    claims: dict = Depends(require_admin),
    service: GoodsReceivedReportService = Depends(get_goods_received_report_service),
) -> GoodsReceivedReportResponse:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date",
        )

    tenant_id = str(claims.get("tenant_id", "1"))
    filters = GoodsReceivedReportFilters(
        start_date=start_date,
        end_date=end_date,
        default_vat_rate=default_vat_rate,
        branch_id=branch_id,
    )

    return await service.get_goods_received_report(tenant_id=tenant_id, filters=filters)


@router.get(
    "/inventory-balance",
    response_model=DailyInventoryBalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Daily Inventory Cost Ledger Report",
    description=(
        "Retrieves consolidated daily inventory balance (Goods Received vs "
        "Shrinkage), "
        "calculates net patrimonial variation (Delta = Altas - Mermas). Exclusive to "
        "administrator role."
    ),
)
async def get_daily_inventory_balance_report(
    start_date: date = Query(
        ..., description="Start date for audit records (inclusive)"
    ),
    end_date: date = Query(..., description="End date for audit records (inclusive)"),
    branch_id: Optional[int] = Query(
        default=None, description="Optional branch ID filter", ge=1
    ),
    claims: dict = Depends(require_admin),
    service: DailyInventoryBalanceReportService = Depends(
        get_daily_inventory_balance_report_service
    ),
) -> DailyInventoryBalanceResponse:
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date",
        )

    tenant_id = str(claims.get("tenant_id", "1"))
    filters = DailyInventoryBalanceFilters(
        start_date=start_date,
        end_date=end_date,
        branch_id=branch_id,
    )

    return await service.get_daily_inventory_balance_report(
        tenant_id=tenant_id, filters=filters
    )
