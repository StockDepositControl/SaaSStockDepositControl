from datetime import date, datetime, time
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.adapters.database.connection import get_analytics_session_factory
from backend.adapters.repositories.models.analytics import AuditRecord as AuditRecordORM
from backend.app.reports.domain import GoodsReceivedRawRecord, ShrinkageRawRecord
from backend.app.reports.ports import (
    GoodsReceivedReportRepositoryPort,
    ShrinkageReportRepositoryPort,
)



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
    SQLAlchemy implementation of GoodsReceivedReportRepositoryPort querying db_analytics.
    Retrieves goods received and addition audit records filtered by tenant, action_type, and date range.
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

