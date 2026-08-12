from typing import List, Optional
from backend.app.branches.models import Branch, BranchCreate, BranchUpdate
from backend.app.branches.ports import BranchRepositoryPort
from backend.app.enterprises.ports import EnterpriseRepositoryPort
from backend.app.exceptions import EntityNotFoundException

class BranchService:
    def __init__(
        self,
        branch_repository: BranchRepositoryPort,
        enterprise_repository: Optional[EnterpriseRepositoryPort] = None
    ):
        self.branch_repository = branch_repository
        self.enterprise_repository = enterprise_repository

    async def get_branch(self, branch_id: int) -> Branch:
        branch = await self.branch_repository.get_by_id(branch_id)
        if not branch:
            raise EntityNotFoundException(f"Branch with id {branch_id} not found")
        return branch

    async def list_branches_by_tenant(self, tenant_id: int) -> List[Branch]:
        return await self.branch_repository.list_by_tenant(tenant_id)

    async def create_branch(self, data: BranchCreate) -> Branch:
        if self.enterprise_repository:
            enterprise = await self.enterprise_repository.get_by_id(data.tenant_id)
            if not enterprise:
                raise EntityNotFoundException(f"Enterprise with tenant_id {data.tenant_id} not found")
        return await self.branch_repository.create(data)

    async def update_branch(self, branch_id: int, data: BranchUpdate) -> Branch:
        updated = await self.branch_repository.update(branch_id, data)
        if not updated:
            raise EntityNotFoundException(f"Branch with id {branch_id} not found")
        return updated

    async def delete_branch(self, branch_id: int) -> bool:
        success = await self.branch_repository.delete(branch_id)
        if not success:
            raise EntityNotFoundException(f"Branch with id {branch_id} not found")
        return success
