from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from backend.app.reports.domain import GoodsReceivedRawRecord, ShrinkageRawRecord


class ShrinkageReportRepositoryPort(ABC):
    """
    Abstract port for retrieving shrinkage audit movement records.
    Decoupled from specific database implementations.
    """

    @abstractmethod
    async def fetch_shrinkage_records(
        self,
        tenant_id: int,
        start_date: date,
        end_date: date,
        branch_id: Optional[int] = None,
    ) -> List[ShrinkageRawRecord]:
        """
        Retrieves all REMOVAL audit records within the given date range for a tenant and optional branch.
        """
        pass


class GoodsReceivedReportRepositoryPort(ABC):
    """
    Abstract port for retrieving goods received / addition audit movement records.
    Decoupled from specific database implementations.
    """

    @abstractmethod
    async def fetch_goods_received_records(
        self,
        tenant_id: int,
        start_date: date,
        end_date: date,
        branch_id: Optional[int] = None,
    ) -> List[GoodsReceivedRawRecord]:
        """
        Retrieves all ADDITION audit records within the given date range for a tenant and optional branch.
        """
        pass

