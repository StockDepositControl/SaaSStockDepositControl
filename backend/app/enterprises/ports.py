from abc import ABC, abstractmethod
from typing import List, Optional

from backend.app.enterprises.models import (
    Enterprise,
    EnterpriseCreate,
    EnterpriseUpdate,
)


class EnterpriseRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, tenant_id: int) -> Optional[Enterprise]:
        """Retrieve an Enterprise by tenant_id."""
        pass

    @abstractmethod
    async def list_all(self) -> List[Enterprise]:
        """List all Enterprises."""
        pass

    @abstractmethod
    async def create(self, data: EnterpriseCreate) -> Enterprise:
        """Create a new Enterprise."""
        pass

    @abstractmethod
    async def update(
        self, tenant_id: int, data: EnterpriseUpdate
    ) -> Optional[Enterprise]:
        """Update an existing Enterprise."""
        pass

    @abstractmethod
    async def delete(self, tenant_id: int) -> bool:
        """Delete an Enterprise by tenant_id."""
        pass
