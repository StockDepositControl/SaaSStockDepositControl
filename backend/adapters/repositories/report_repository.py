from collections import defaultdict
from datetime import date, datetime, time
from decimal import Decimal
from typing import Dict, List, Optional

from backend.adapters.database.connection import get_analytics_session_factory
from backend.adapters.repositories.models.analytics import (
    AuditRecord as AuditRecordORM,
)
from backend.adapters.repositories.models.analytics import (
    DailyReport as DailyReportORM,
)
from backend.app.reports.domain import (
    DailyInventoryBalanceRecord,
    GoodsReceivedRawRecord,
    ShrinkageRawRecord,
)
from backend.app.reports.ports import (
    DailyInventoryBalanceReportRepositoryPort,
    GoodsReceivedReportRepositoryPort,
    ShrinkageReportRepositoryPort,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker


class SQLAlchemyShrinkageReportRepository(ShrinkageReportRepositoryPort):
    """
    SQLAlchemy implementation of ShrinkageReportRepositoryPort querying db_analytics.
    Retrieves shrinkage audit records filtered by tenant, action_type, and date range.
    """

    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_analytics_session_factory()

    async def fetch_shrinkage_records(
        self,
        tenant_id: int,
        start_date: date,
        end_date: date,
        branch_id: Optional[int] = None,
    ) -> List[ShrinkageRawRecord]:
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)

        async with self.session_factory() as session:
            stmt = select(AuditRecordORM).where(
                AuditRecordORM.tenant_id == tenant_id,
                AuditRecordORM.action_type.in_(["REMOVAL", "BAJA", "Baja"]),
                AuditRecordORM.scan_timestamp >= start_dt,
                AuditRecordORM.scan_timestamp <= end_dt,
            )

            if branch_id is not None:
                stmt = stmt.where(AuditRecordORM.branch_id == branch_id)

            stmt = stmt.order_by(AuditRecordORM.scan_timestamp.asc())
            result = await session.execute(stmt)
            rows = result.scalars().all()

            return [
                ShrinkageRawRecord(
                    audit_id=row.audit_id,
                    article_code=row.article_code,
                    affected_amount=row.affected_amount,
                    applied_unit_cost=row.applied_unit_cost,
                    applied_vat_rate=row.applied_vat_rate,
                    valorized_amount=row.valorized_amount,
                    scan_timestamp=row.scan_timestamp,
                    branch_id=row.branch_id,
                )
                for row in rows
            ]


class SQLAlchemyGoodsReceivedReportRepository(GoodsReceivedReportRepositoryPort):
    """
    SQLAlchemy implementation of GoodsReceivedReportRepositoryPort querying
    db_analytics.
    Retrieves goods received and addition audit records filtered by tenant, action_type,
    and date range.
    """

    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_analytics_session_factory()

    async def fetch_goods_received_records(
        self,
        tenant_id: int,
        start_date: date,
        end_date: date,
        branch_id: Optional[int] = None,
    ) -> List[GoodsReceivedRawRecord]:
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)

        async with self.session_factory() as session:
            stmt = select(AuditRecordORM).where(
                AuditRecordORM.tenant_id == tenant_id,
                AuditRecordORM.action_type.in_(["ADDITION", "ALTA", "Alta"]),
                AuditRecordORM.scan_timestamp >= start_dt,
                AuditRecordORM.scan_timestamp <= end_dt,
            )

            if branch_id is not None:
                stmt = stmt.where(AuditRecordORM.branch_id == branch_id)

            stmt = stmt.order_by(AuditRecordORM.scan_timestamp.asc())
            result = await session.execute(stmt)
            rows = result.scalars().all()

            return [
                GoodsReceivedRawRecord(
                    audit_id=row.audit_id,
                    article_code=row.article_code,
                    affected_amount=row.affected_amount,
                    applied_unit_cost=row.applied_unit_cost,
                    applied_vat_rate=row.applied_vat_rate,
                    valorized_amount=row.valorized_amount,
                    scan_timestamp=row.scan_timestamp,
                    branch_id=row.branch_id,
                    observation=row.observation,
                )
                for row in rows
            ]


class SQLAlchemyDailyInventoryBalanceReportRepository(
    DailyInventoryBalanceReportRepositoryPort
):
    """
    SQLAlchemy implementation of DailyInventoryBalanceReportRepositoryPort querying
    db_analytics.
    Retrieves consolidated daily inventory balance records from DailyReport ORM,
    with dynamic aggregation fallback from AuditRecordORM if no pre-aggregated records
    exist.
    """

    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_analytics_session_factory()

    async def fetch_daily_balance_records(
        self,
        tenant_id: int,
        start_date: date,
        end_date: date,
        branch_id: Optional[int] = None,
    ) -> List[DailyInventoryBalanceRecord]:
        async with self.session_factory() as session:
            stmt = select(DailyReportORM).where(
                DailyReportORM.tenant_id == tenant_id,
                DailyReportORM.report_date >= start_date,
                DailyReportORM.report_date <= end_date,
            )

            if branch_id is not None:
                stmt = stmt.where(DailyReportORM.branch_id == branch_id)

            stmt = stmt.order_by(
                DailyReportORM.report_date.asc(), DailyReportORM.branch_id.asc()
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

            if rows:
                return [
                    DailyInventoryBalanceRecord(
                        tenant_id=row.tenant_id,
                        branch_id=row.branch_id,
                        report_date=row.report_date,
                        total_audit_articles=row.total_audit_articles,
                        total_processed_units=row.total_processed_units,
                        total_addition_amount=row.total_addition_amount,
                        total_shrinkage_amount=row.total_shrinkage_amount,
                        total_addition_value=row.total_addition_value,
                        total_shrinkage_value=row.total_shrinkage_value,
                        net_patrimonial_variation=row.net_patrimonial_variation,
                    )
                    for row in rows
                ]

            # Dynamic aggregation fallback from AuditRecordORM
            start_dt = datetime.combine(start_date, time.min)
            end_dt = datetime.combine(end_date, time.max)

            audit_stmt = select(AuditRecordORM).where(
                AuditRecordORM.tenant_id == tenant_id,
                AuditRecordORM.scan_timestamp >= start_dt,
                AuditRecordORM.scan_timestamp <= end_dt,
            )

            if branch_id is not None:
                audit_stmt = audit_stmt.where(AuditRecordORM.branch_id == branch_id)

            audit_stmt = audit_stmt.order_by(AuditRecordORM.scan_timestamp.asc())
            audit_result = await session.execute(audit_stmt)
            audit_rows = audit_result.scalars().all()

            if not audit_rows:
                return []

            grouped_data: Dict[tuple, dict] = defaultdict(
                lambda: {
                    "articles": set(),
                    "total_processed_units": 0,
                    "total_addition_amount": 0,
                    "total_shrinkage_amount": 0,
                    "total_addition_value": Decimal("0.00"),
                    "total_shrinkage_value": Decimal("0.00"),
                }
            )

            for rec in audit_rows:
                rec_date = rec.scan_timestamp.date()
                rec_branch = rec.branch_id
                key = (rec_date, rec_branch)
                group = grouped_data[key]

                group["articles"].add(rec.article_code)
                group["total_processed_units"] += rec.affected_amount

                action = rec.action_type
                if action in ("ADDITION", "ALTA", "Alta"):
                    group["total_addition_amount"] += rec.affected_amount
                    group["total_addition_value"] += Decimal(str(rec.valorized_amount))
                elif action in ("REMOVAL", "BAJA", "Baja"):
                    group["total_shrinkage_amount"] += rec.affected_amount
                    group["total_shrinkage_value"] += Decimal(str(rec.valorized_amount))

            records: List[DailyInventoryBalanceRecord] = []
            for rec_date, rec_branch in sorted(
                grouped_data.keys(), key=lambda k: (k[0], k[1])
            ):
                data = grouped_data[(rec_date, rec_branch)]
                net_variation = (
                    data["total_addition_value"] - data["total_shrinkage_value"]
                )
                records.append(
                    DailyInventoryBalanceRecord(
                        tenant_id=tenant_id,
                        branch_id=rec_branch,
                        report_date=rec_date,
                        total_audit_articles=len(data["articles"]),
                        total_processed_units=data["total_processed_units"],
                        total_addition_amount=data["total_addition_amount"],
                        total_shrinkage_amount=data["total_shrinkage_amount"],
                        total_addition_value=data["total_addition_value"],
                        total_shrinkage_value=data["total_shrinkage_value"],
                        net_patrimonial_variation=net_variation,
                    )
                )

            return records
