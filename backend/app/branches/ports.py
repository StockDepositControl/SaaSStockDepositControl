from abc import ABC, abstractmethod
from typing import List, Optional
from backend.app.branches.models import Branch, BranchCreate, BranchUpdate

class BranchRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, branch_id: int) -> Optional[Branch]:
        """Retrieve a Branch by branch_id."""
        pass

    @abstractmethod
    async def list_by_tenant(self, tenant_id: int) -> List[Branch]:
        """List all Branches for a given tenant_id."""
        pass

    @abstractmethod
    async def create(self, data: BranchCreate) -> Branch:
        """Create a new Branch within an Enterprise."""
        pass

    @abstractmethod
    async def update(self, branch_id: int, data: BranchUpdate) -> Optional[Branch]:
        """Update an existing Branch."""
        pass

    @abstractmethod
    async def delete(self, branch_id: int) -> bool:
        """Delete a Branch by branch_id."""
        pass
