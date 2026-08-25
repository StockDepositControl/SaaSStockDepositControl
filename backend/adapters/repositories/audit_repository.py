from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.app.movements.domain import AuditRecordCreate, AuditRecord, TipoAccion
from backend.app.movements.ports import AuditRepositoryPort
from backend.adapters.repositories.models.analytics import AuditRecord as AuditRecordORM, ActionType as ActionTypeORM
from backend.adapters.database.connection import get_analytics_session_factory

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

    async def create_audit_record(
        self, record: AuditRecordCreate
    ) -> AuditRecord:
        async with self.session_factory() as session:
            try:
                numeric_tenant_id = int(record.tenant_id)
            except (ValueError, TypeError):
                numeric_tenant_id = 1

            orm_record = AuditRecordORM(
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

    async def exists_by_client_uuid(
        self, client_uuid: str
    ) -> bool:
        if not client_uuid:
            return False

        async with self.session_factory() as session:
            stmt = select(AuditRecordORM).where(AuditRecordORM.client_uuid == client_uuid)
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

