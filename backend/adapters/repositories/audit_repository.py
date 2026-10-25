from decimal import Decimal
from typing import Dict, List, Optional

from backend.adapters.database.connection import get_analytics_session_factory
from backend.adapters.repositories.models.analytics import ActionType as ActionTypeORM
from backend.adapters.repositories.models.analytics import AuditRecord as AuditRecordORM
from backend.app.movements.domain import (
    AuditRecord,
    AuditRecordCreate,
    SessionAuditAggregates,
    TipoAccion,
)
from backend.app.movements.ports import AuditRepositoryPort
from sqlalchemy import case, distinct, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker


class SQLAlchemyAuditRepository(AuditRepositoryPort):
    """
    SQLAlchemy implementation of AuditRepositoryPort managing db_analytics audit logs.
    """

    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_analytics_session_factory()

    def _map_action_type(self, tipo: TipoAccion) -> str:
        if tipo == TipoAccion.ALTA:
            return ActionTypeORM.ADDITION.value
        elif tipo == TipoAccion.BAJA:
            return ActionTypeORM.REMOVAL.value
        else:
            return ActionTypeORM.NO_ACTION.value

    def _map_action_type_to_domain(self, action: str) -> TipoAccion:
        if action in (ActionTypeORM.ADDITION, ActionTypeORM.ADDITION.value):
            return TipoAccion.ALTA
        elif action in (ActionTypeORM.REMOVAL, ActionTypeORM.REMOVAL.value):
            return TipoAccion.BAJA
        else:
            return TipoAccion.SIN_ACCION

    async def create_audit_record(self, record: AuditRecordCreate) -> AuditRecord:
        async with self.session_factory() as session:
            try:
                numeric_tenant_id = int(record.tenant_id)
            except (ValueError, TypeError):
                numeric_tenant_id = 1

            orm_record = AuditRecordORM(
                session_id=record.session_id,
                tenant_id=numeric_tenant_id,
                branch_id=record.branch_id,
                warehouse_id=record.warehouse_id,
                article_code=record.article_code,
                user_id=record.user_id,
                action_type=self._map_action_type(record.action_type),
                affected_amount=record.affected_amount,
                audit_quantity=record.audit_quantity,
                applied_unit_cost=record.applied_unit_cost,
                applied_vat_rate=record.applied_vat_rate,
                valorized_amount=record.valorized_amount,
                scan_timestamp=record.scan_timestamp,
                client_uuid=record.client_uuid,
                observation=record.observation,
            )
            session.add(orm_record)
            await session.commit()
            await session.refresh(orm_record)

            return AuditRecord(
                audit_id=orm_record.audit_id,
                session_id=orm_record.session_id,
                tenant_id=orm_record.tenant_id,
                branch_id=orm_record.branch_id,
                warehouse_id=orm_record.warehouse_id or record.warehouse_id,
                article_code=orm_record.article_code,
                action_type=self._map_action_type_to_domain(orm_record.action_type),
                affected_amount=orm_record.affected_amount,
                audit_quantity=orm_record.audit_quantity,
                applied_unit_cost=orm_record.applied_unit_cost,
                applied_vat_rate=orm_record.applied_vat_rate,
                valorized_amount=orm_record.valorized_amount,
                user_id=orm_record.user_id,
                scan_timestamp=orm_record.scan_timestamp,
                client_uuid=orm_record.client_uuid,
                observation=orm_record.observation,
            )

    async def exists_by_client_uuid(self, client_uuid: str) -> bool:
        if not client_uuid:
            return False

        async with self.session_factory() as session:
            stmt = select(AuditRecordORM).where(
                AuditRecordORM.client_uuid == client_uuid
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def get_latest_audit_record(
        self, tenant_id: int, id_sucursal: int, id_deposito: int, id_articulo: str
    ) -> Optional[AuditRecord]:
        async with self.session_factory() as session:
            numeric_tenant_id = tenant_id

            stmt = (
                select(AuditRecordORM)
                .where(
                    AuditRecordORM.tenant_id == numeric_tenant_id,
                    AuditRecordORM.branch_id == id_sucursal,
                    AuditRecordORM.warehouse_id == id_deposito,
                    AuditRecordORM.article_code == id_articulo,
                )
                .order_by(AuditRecordORM.scan_timestamp.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            orm_record = result.scalar_one_or_none()

            if not orm_record:
                return None

            return AuditRecord(
                audit_id=orm_record.audit_id,
                session_id=orm_record.session_id,
                tenant_id=orm_record.tenant_id,
                branch_id=orm_record.branch_id,
                warehouse_id=orm_record.warehouse_id or id_deposito,
                article_code=orm_record.article_code,
                action_type=self._map_action_type_to_domain(orm_record.action_type),
                affected_amount=orm_record.affected_amount,
                audit_quantity=orm_record.audit_quantity,
                applied_unit_cost=orm_record.applied_unit_cost,
                applied_vat_rate=orm_record.applied_vat_rate,
                valorized_amount=orm_record.valorized_amount,
                user_id=orm_record.user_id,
                scan_timestamp=orm_record.scan_timestamp,
                client_uuid=orm_record.client_uuid,
                observation=orm_record.observation,
            )

    async def get_latest_audits_for_articles(
        self, session_id: int, article_ids: List[str]
    ) -> Dict[str, int]:
        if not article_ids:
            return {}

        async with self.session_factory() as session:
            rn = (
                func.row_number()
                .over(
                    partition_by=AuditRecordORM.article_code,
                    order_by=AuditRecordORM.scan_timestamp.desc(),
                )
                .label("rn")
            )

            subq = (
                select(AuditRecordORM.article_code, AuditRecordORM.audit_quantity, rn)
                .where(
                    AuditRecordORM.session_id == session_id,
                    AuditRecordORM.article_code.in_(article_ids),
                )
                .subquery()
            )

            stmt = select(subq.c.article_code, subq.c.audit_quantity).where(
                subq.c.rn == 1
            )
            result = await session.execute(stmt)
            rows = result.all()
            return {
                str(row[0]).strip(): (int(row[1]) if row[1] is not None else 0)
                for row in rows
            }

    async def get_session_audit_aggregates(
        self, tenant_id: int, branch_id: int, deposit_id: int, session_id: int
    ) -> SessionAuditAggregates:
        def distinct_articles_for(action: ActionTypeORM):
            return func.count(
                distinct(
                    case(
                        (
                            AuditRecordORM.action_type == action.value,
                            AuditRecordORM.article_code,
                        ),
                        else_=None,
                    )
                )
            )

        def amount_for(action: ActionTypeORM):
            return func.coalesce(
                func.sum(
                    case(
                        (
                            AuditRecordORM.action_type == action.value,
                            AuditRecordORM.valorized_amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            )

        stmt = select(
            func.count(distinct(AuditRecordORM.article_code)),
            distinct_articles_for(ActionTypeORM.ADDITION),
            distinct_articles_for(ActionTypeORM.REMOVAL),
            distinct_articles_for(ActionTypeORM.NO_ACTION),
            amount_for(ActionTypeORM.REMOVAL),
            amount_for(ActionTypeORM.ADDITION),
        ).where(
            AuditRecordORM.session_id == session_id,
            AuditRecordORM.tenant_id == tenant_id,
            AuditRecordORM.branch_id == branch_id,
            AuditRecordORM.warehouse_id == deposit_id,
        )

        async with self.session_factory() as session:
            row = (await session.execute(stmt)).one()

        return SessionAuditAggregates(
            audited_count=int(row[0] or 0),
            alta_count=int(row[1] or 0),
            baja_count=int(row[2] or 0),
            sin_accion_count=int(row[3] or 0),
            monto_valorizado_baja=Decimal(str(row[4] or 0)),
            monto_valorizado_alta=Decimal(str(row[5] or 0)),
        )
