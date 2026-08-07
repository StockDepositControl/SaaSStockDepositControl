import enum
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    DECIMAL as SQLDecimal,
    DateTime,
    Date,
    Enum,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseAnalytics(DeclarativeBase):
    pass


class ActionType(str, enum.Enum):
    ADDITION = "ADDITION"
    REMOVAL = "REMOVAL"
    NO_ACTION = "NO_ACTION"


class RiskLevel(str, enum.Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class RecordTenant(BaseAnalytics):
    __tablename__ = "record_tenants"

    tenant_id: Mapped[int] = mapped_column(Integer().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    tenant_name: Mapped[str] = mapped_column(String(150), nullable=False)
    pharmacy_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    audit_records: Mapped[List["AuditRecord"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    daily_reports: Mapped[List["DailyReport"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    critical_shrinkage_alerts: Mapped[List["CriticalShrinkageAlert"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class AuditRecord(BaseAnalytics):
    __tablename__ = "audit_records"

    audit_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("record_tenants.tenant_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, nullable=True)
    article_code: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    affected_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    audit_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    applied_unit_cost: Mapped[Decimal] = mapped_column(SQLDecimal(15, 4), nullable=False)
    applied_vat_rate: Mapped[Decimal] = mapped_column(SQLDecimal(5, 4), nullable=False)
    valorized_amount: Mapped[Decimal] = mapped_column(SQLDecimal(15, 4), nullable=False)
    scan_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    client_uuid: Mapped[Optional[str]] = mapped_column(String(36), unique=True, nullable=True)
    observation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    tenant: Mapped["RecordTenant"] = relationship(back_populates="audit_records")

    __table_args__ = (
        Index("idx_audit_tenant_scan", "tenant_id", "scan_timestamp"),
        Index("idx_audit_article", "article_code"),
        Index("idx_audit_tenant_client_uuid", "tenant_id", "client_uuid"),
        Index("idx_audit_fallback", "tenant_id", "branch_id", "warehouse_id", "article_code", "scan_timestamp"),
    )



class DailyReport(BaseAnalytics):
    __tablename__ = "daily_reports"

    daily_report_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("record_tenants.tenant_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_audit_articles: Mapped[int] = mapped_column(Integer, nullable=False)
    total_addition_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    total_shrinkage_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    total_addition_value: Mapped[Decimal] = mapped_column(SQLDecimal(15, 4), nullable=False)
    total_shrinkage_value: Mapped[Decimal] = mapped_column(SQLDecimal(15, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant: Mapped["RecordTenant"] = relationship(back_populates="daily_reports")

    __table_args__ = (
        Index("idx_daily_reports_tenant_date", "tenant_id", "report_date", unique=True),
    )


class CriticalShrinkageAlert(BaseAnalytics):
    __tablename__ = "critical_shrinkage_alerts"

    alert_id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("record_tenants.tenant_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(Integer, nullable=False)
    article_code: Mapped[str] = mapped_column(String(100), nullable=False)
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_to_expiration: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False)
    stock_at_risk: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_at_risk: Mapped[Decimal] = mapped_column(SQLDecimal(15, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    tenant: Mapped["RecordTenant"] = relationship(back_populates="critical_shrinkage_alerts")

    __table_args__ = (
        Index("idx_alerts_tenant_risk", "tenant_id", "risk_level", "expiration_date"),
    )
