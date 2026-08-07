from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, Tuple
from backend.app.movements.models import StockPorDeposito, AuditRecordCreate, AuditRecord

class StockRepositoryPort(ABC):
    """
    Abstract port for reading stock position and article cost data.
    Decoupled from specific database implementations.
    """
    @abstractmethod
    async def get_stock_position(
        self, tenant_id: str, id_sucursal: int, id_deposito: int, id_articulo: str, id_empresa: Optional[int] = None
    ) -> Optional[StockPorDeposito]:
        """
        Retrieves current stock position (stock_real) for a specific deposit and article.
        """
        pass


    @abstractmethod
    async def get_article_cost_info(
        self, tenant_id: str, id_articulo: str
    ) -> Tuple[Decimal, str]:
        """
        Retrieves article purchase cost (pcio_com_siva) and family description (des_familia).
        Returns tuple: (pcio_com_siva, des_familia).
        """
        pass


class AuditRepositoryPort(ABC):
    """
    Abstract port for persisting audit logs and managing audit idempotency.
    Decoupled from specific database implementations.
    """
    @abstractmethod
    async def create_audit_record(
        self, record: AuditRecordCreate
    ) -> AuditRecord:
        """
        Persists a new audit movement record in db_analytics.
        """
        pass

    @abstractmethod
    async def exists_by_client_uuid(
        self, tenant_id: str, client_uuid: str
    ) -> bool:
        """
        Checks whether an audit record with the given client_uuid already exists for idempotency.
        """
        pass

    @abstractmethod
    async def get_latest_audit_record(
        self, tenant_id: str, id_sucursal: int, id_deposito: int, id_articulo: str
    ) -> Optional[AuditRecord]:
        """
        Retrieves the most recent audit record for an article in a specific deposit.
        """
        pass
