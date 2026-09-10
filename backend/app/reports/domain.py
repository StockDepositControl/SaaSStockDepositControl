from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict



class VatCalculator:
    """
    Pure Fabrication domain service encapsulating VAT fiscal adjustments and valorization math.
    Stateless and free of any infrastructure or database dependencies.
    """

    @staticmethod
    def calculate_total_unit_cost(pcio_com_siva: Decimal, vat_rate: Decimal) -> Decimal:
        """
        Computes the total unit cost including VAT:
        total_unit_cost = pcio_com_siva * (1 + vat_rate)
        """
        return pcio_com_siva * (Decimal("1.00") + vat_rate)

    @staticmethod
    def calculate_financial_loss(quantity: int, total_unit_cost: Decimal) -> Decimal:
        """
        Computes total financial loss for an affected stock quantity:
        total_loss = quantity * total_unit_cost
        """
        return Decimal(str(quantity)) * total_unit_cost


class ShrinkageRawRecord(BaseModel):
    """
    Pure domain representation of an individual shrinkage movement record from the audit ledger.
    """
    audit_id: int
    article_code: str
    affected_amount: int
    applied_unit_cost: Decimal
    applied_vat_rate: Decimal
    valorized_amount: Decimal
    scan_timestamp: datetime
    branch_id: int

    model_config = ConfigDict(from_attributes=True)


class GoodsReceivedRawRecord(BaseModel):
    """
    Pure domain representation of an individual goods received / addition movement record from the audit ledger.
    """
    audit_id: int
    article_code: str
    affected_amount: int
    applied_unit_cost: Decimal
    applied_vat_rate: Decimal
    valorized_amount: Decimal
    scan_timestamp: datetime
    branch_id: int
    observation: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DailyInventoryBalanceRecord(BaseModel):
    """
    Pure domain representation of daily consolidated inventory balance data per branch.
    """
    tenant_id: int
    branch_id: int
    report_date: date
    total_audit_articles: int
    total_processed_units: int
    total_addition_amount: int
    total_shrinkage_amount: int
    total_addition_value: Decimal
    total_shrinkage_value: Decimal
    net_patrimonial_variation: Decimal

    model_config = ConfigDict(from_attributes=True)

