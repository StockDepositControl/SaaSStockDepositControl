from typing import List
from backend.app.enterprises.models import Enterprise, EnterpriseCreate, EnterpriseUpdate
from backend.app.enterprises.ports import EnterpriseRepositoryPort
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException

class EnterpriseService:
    def __init__(self, enterprise_repository: EnterpriseRepositoryPort):
        self.enterprise_repository = enterprise_repository

    async def get_enterprise(self, tenant_id: int) -> Enterprise:
        enterprise = await self.enterprise_repository.get_by_id(tenant_id)
        if not enterprise:
            raise EntityNotFoundException(f"Enterprise with tenant_id {tenant_id} not found")
        return enterprise

    async def list_enterprises(self) -> List[Enterprise]:
        return await self.enterprise_repository.list_all()

    async def create_enterprise(self, data: EnterpriseCreate) -> Enterprise:
        existing = await self.enterprise_repository.get_by_id(data.tenant_id)
        if existing:
            raise BusinessRuleViolationException(f"Enterprise with tenant_id {data.tenant_id} already exists")
        return await self.enterprise_repository.create(data)

    async def update_enterprise(self, tenant_id: int, data: EnterpriseUpdate) -> Enterprise:
        updated = await self.enterprise_repository.update(tenant_id, data)
        if not updated:
            raise EntityNotFoundException(f"Enterprise with tenant_id {tenant_id} not found")
        return updated

    async def delete_enterprise(self, tenant_id: int) -> bool:
        success = await self.enterprise_repository.delete(tenant_id)
        if not success:
            raise EntityNotFoundException(f"Enterprise with tenant_id {tenant_id} not found")
        return success
