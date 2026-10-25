from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ShrinkageReportFilters(BaseModel):
    """
    Filter parameters for shrinkage report generation.
    """

    start_date: date = Field(..., description="Start date (inclusive)")
    end_date: date = Field(..., description="End date (inclusive)")
    default_vat_rate: Decimal = Field(
        default=Decimal("0.21"),
        description="Default VAT rate applied to non-exempt item families",
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
    )
    branch_id: Optional[int] = Field(
        default=None,
        description="Optional branch ID filter",
        ge=1,
    )


class ShrinkageLineItem(BaseModel):
    """
    Aggregated shrinkage metrics per article catalog entry.
    """

    article_code: str
    des_articulo: str
    des_familia: str
    pcio_com_siva: Decimal
    vat_rate: Decimal
    total_unit_cost: Decimal
    total_quantity: int
    total_financial_loss: Decimal

    model_config = ConfigDict(from_attributes=True)


class ShrinkageReportResponse(BaseModel):
    """
    Complete consolidated shrinkage and financial erosion report output.
    Exclusively returned to authorized administrative roles.
    """

    tenant_id: str
    start_date: date
    end_date: date
    default_vat_rate: Decimal
    total_items: int
    total_shrinkage_units: int
    total_financial_erosion: Decimal
    line_items: List[ShrinkageLineItem]

    model_config = ConfigDict(from_attributes=True)


class GoodsReceivedReportFilters(BaseModel):
    """
    Filter parameters for goods received report generation.
    """

    start_date: date = Field(..., description="Start date (inclusive)")
    end_date: date = Field(..., description="End date (inclusive)")
    default_vat_rate: Decimal = Field(
        default=Decimal("0.21"),
        description="Default VAT rate applied to non-exempt item families",
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
    )
    branch_id: Optional[int] = Field(
        default=None,
        description="Optional branch ID filter",
        ge=1,
    )


class GoodsReceivedLineItem(BaseModel):
    """
    Goods received and addition metrics per article catalog entry.
    """

    barcode: str
    article_code: str
    des_articulo: str
    des_familia: str
    reason: str
    quantity_added: int
    pcio_com_siva: Decimal
    vat_rate: Decimal
    total_unit_cost: Decimal
    capital_inyectado: Decimal

    model_config = ConfigDict(from_attributes=True)


class GoodsReceivedReportResponse(BaseModel):
    """
    Complete consolidated goods received and injected capital valorization report
    output.
    Exclusively returned to authorized administrative roles.
    """

    tenant_id: str
    start_date: date
    end_date: date
    default_vat_rate: Decimal
    total_items: int
    total_added_units: int
    total_capital_inyectado: Decimal
    line_items: List[GoodsReceivedLineItem]

    model_config = ConfigDict(from_attributes=True)


class DailyInventoryBalanceFilters(BaseModel):
    """
    Filter parameters for daily inventory balance report generation.
    """

    start_date: date = Field(..., description="Start date (inclusive)")
    end_date: date = Field(..., description="End date (inclusive)")
    branch_id: Optional[int] = Field(
        default=None,
        description="Optional branch ID filter",
        ge=1,
    )


class DailyInventoryBalanceSummary(BaseModel):
    """
    Summary metrics per day for inventory balance.
    """

    report_date: date
    total_audit_articles: int
    total_processed_units: int
    total_addition_units: int
    total_shrinkage_units: int
    total_addition_value: Decimal
    total_shrinkage_value: Decimal
    net_patrimonial_variation: Decimal

    model_config = ConfigDict(from_attributes=True)


class DailyInventoryBalanceResponse(BaseModel):
    """
    Consolidated daily inventory balance report response.
    Exclusively returned to authorized administrative roles.
    """

    tenant_id: str
    branch_id: Optional[int] = None
    start_date: date
    end_date: date
    total_days: int
    total_addition_value: Decimal
    total_shrinkage_value: Decimal
    net_patrimonial_variation: Decimal
    daily_summaries: List[DailyInventoryBalanceSummary]

    model_config = ConfigDict(from_attributes=True)
