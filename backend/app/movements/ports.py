from abc import ABC, abstractmethod
from typing import Optional, List, Dict
from backend.app.movements.domain import (
    StockPorDeposito,
    AuditRecordCreate,
    AuditRecord,
    SessionAuditAggregates,
)

class StockRepositoryPort(ABC):
    """
    Abstract port for reading stock position data.
    Decoupled from specific database implementations.
    """
    @abstractmethod
    async def get_stock_position(
        self, tenant_id: int, id_sucursal: int, id_deposito: int, id_articulo: str
    ) -> Optional[StockPorDeposito]:
        """
        Retrieves current stock position (stock_real) for a specific deposit and article.
        """
        pass

    @abstractmethod
    async def get_stock_positions_batch(
        self, deposit_id: int, article_ids: List[str]
    ) -> Dict[str, int]:
        """
        Retrieves current stock positions (stock_real) for multiple articles in a specific deposit.
        Automatically filters by ContextVar(tenant_id, branch_id).
        Returns a mapping of {id_articulo: stock_real}.
        """
        pass

    @abstractmethod
    async def count_catalog_articles(self) -> int:
        """
        Returns the total number of articles in the catalog (articulos).
        The articulos table is a shared legacy catalog with no tenant column.
        """
        pass

    @abstractmethod
    async def count_out_of_stock_articles(
        self, tenant_id: int, branch_id: int, deposit_id: int
    ) -> int:
        """
        Returns how many stock positions have stock_real == 0 for the given deposit.
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
        self, client_uuid: str
    ) -> bool:
        """
        Checks whether an audit record with the given client_uuid already exists for idempotency.
        """
        pass

    @abstractmethod
    async def get_latest_audit_record(
        self, tenant_id: int, id_sucursal: int, id_deposito: int, id_articulo: str
    ) -> Optional[AuditRecord]:
        """
        Retrieves the most recent audit record for an article in a specific deposit.
        """
        pass

    @abstractmethod
    async def get_latest_audits_for_articles(
        self, session_id: int, article_ids: List[str]
    ) -> Dict[str, int]:
        """
        Retrieves the latest audit quantity for multiple articles within a specific session.
        Returns a mapping of {id_articulo: audit_quantity}.
        """
        pass

    @abstractmethod
    async def get_session_audit_aggregates(
        self, tenant_id: int, branch_id: int, deposit_id: int, session_id: int
    ) -> SessionAuditAggregates:
        """
        Returns audit counters (distinct audited articles, per-action counts and
        valorized amounts) for a work session, aggregated in the database.
        """
        pass

