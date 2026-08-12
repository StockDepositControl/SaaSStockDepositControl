import pytest
from unittest.mock import AsyncMock

from backend.app.enterprises.models import Enterprise, EnterpriseCreate, EnterpriseUpdate
from backend.app.enterprises.services import EnterpriseService
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException

@pytest.mark.asyncio
async def test_enterprise_service_create_success():
    repo = AsyncMock()
    repo.get_by_id.return_value = None
    repo.create.return_value = Enterprise(tenant_id=1, description="Test Enterprise")

    service = EnterpriseService(enterprise_repository=repo)
    data = EnterpriseCreate(tenant_id=1, description="Test Enterprise")
    result = await service.create_enterprise(data)

    assert result.tenant_id == 1
    assert result.description == "Test Enterprise"
    repo.create.assert_called_once_with(data)

@pytest.mark.asyncio
async def test_enterprise_service_create_already_exists():
    repo = AsyncMock()
    repo.get_by_id.return_value = Enterprise(tenant_id=1, description="Existing Enterprise")

    service = EnterpriseService(enterprise_repository=repo)
    data = EnterpriseCreate(tenant_id=1, description="Test Enterprise")

    with pytest.raises(BusinessRuleViolationException):
        await service.create_enterprise(data)

@pytest.mark.asyncio
async def test_enterprise_service_get_not_found():
    repo = AsyncMock()
    repo.get_by_id.return_value = None

    service = EnterpriseService(enterprise_repository=repo)
    with pytest.raises(EntityNotFoundException):
        await service.get_enterprise(999)
