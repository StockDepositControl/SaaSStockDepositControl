from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.app.movements.models import AuditoriaRegistroCreate, AuditoriaRegistro, TipoAccion
from backend.app.movements.ports import AuditRepositoryPort
from backend.adapters.repositories.models.analytics import AuditRecord as AuditRecordORM, ActionType as ActionTypeORM
from backend.adapters.database.connection import get_analytics_session_factory

class SQLAlchemyAuditRepository(AuditRepositoryPort):
    """
    SQLAlchemy implementation of AuditRepositoryPort managing db_analytics audit logs.
    """
    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_analytics_session_factory()

    def _map_action_type(self, tipo: TipoAccion) -> ActionTypeORM:
        if tipo == TipoAccion.ALTA:
            return ActionTypeORM.ADDITION
        elif tipo == TipoAccion.BAJA:
            return ActionTypeORM.REMOVAL
        else:
            return ActionTypeORM.NO_ACTION

    def _map_action_type_to_domain(self, action: ActionTypeORM) -> TipoAccion:
        if action == ActionTypeORM.ADDITION:
            return TipoAccion.ALTA
        elif action == ActionTypeORM.REMOVAL:
            return TipoAccion.BAJA
        else:
            return TipoAccion.SIN_ACCION

    async def create_audit_record(
        self, record: AuditoriaRegistroCreate
    ) -> AuditoriaRegistro:
        async with self.session_factory() as session:
            # Parse tenant_id to int if required by analytics tenant relation schema
            try:
                numeric_tenant_id = int(record.tenant_id)
            except (ValueError, TypeError):
                numeric_tenant_id = 1

            orm_record = AuditRecordORM(
                tenant_id=numeric_tenant_id,
                warehouse_id=record.id_deposito,
                article_code=record.id_articulo,
                user_id=record.id_usuario,
                action_type=self._map_action_type(record.tipo_accion),
                affected_amount=record.cantidad_afectada,
                applied_unit_cost=record.monto_valorizado,
                applied_vat_rate=0,
                valorized_amount=record.monto_valorizado,
                scan_timestamp=record.fecha_hora,
                client_uuid=record.client_uuid,
            )
            session.add(orm_record)
            await session.commit()
            await session.refresh(orm_record)

            return AuditoriaRegistro(
                id_auditoria=orm_record.audit_id,
                tenant_id=record.tenant_id,
                id_sucursal=record.id_sucursal,
                id_deposito=record.id_deposito,
                id_articulo=record.id_articulo,
                tipo_accion=record.tipo_accion,
                cantidad_afectada=record.cantidad_afectada,
                monto_valorizado=record.monto_valorizado,
                id_usuario=record.id_usuario,
                fecha_hora=record.fecha_hora,
                client_uuid=orm_record.client_uuid,
            )

    async def exists_by_client_uuid(
        self, tenant_id: str, client_uuid: str
    ) -> bool:
        if not client_uuid:
            return False

        async with self.session_factory() as session:
            stmt = select(AuditRecordORM).where(AuditRecordORM.client_uuid == client_uuid)
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

