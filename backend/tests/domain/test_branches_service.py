from unittest.mock import AsyncMock

import pytest
from backend.app.branches.models import Branch, BranchCreate
from backend.app.branches.services import BranchService
from backend.app.enterprises.models import Enterprise
from backend.app.exceptions import EntityNotFoundException


@pytest.mark.asyncio
async def test_branch_service_create_success():
    enterprise_repo = AsyncMock()
    enterprise_repo.get_by_id.return_value = Enterprise(
        tenant_id=1, description="Parent Enterprise"
    )

    branch_repo = AsyncMock()
    branch_repo.create.return_value = Branch(
        id_branch=10, tenant_id=1, description="Central Branch"
    )

    service = BranchService(
        branch_repository=branch_repo, enterprise_repository=enterprise_repo
    )
    data = BranchCreate(tenant_id=1, description="Central Branch")
    result = await service.create_branch(data)

    assert result.id_branch == 10
    assert result.tenant_id == 1
    assert result.description == "Central Branch"


@pytest.mark.asyncio
async def test_branch_service_create_enterprise_not_found():
    enterprise_repo = AsyncMock()
    enterprise_repo.get_by_id.return_value = None

    branch_repo = AsyncMock()

    service = BranchService(
        branch_repository=branch_repo, enterprise_repository=enterprise_repo
    )
    data = BranchCreate(tenant_id=999, description="Central Branch")

    with pytest.raises(EntityNotFoundException):
        await service.create_branch(data)


@pytest.mark.asyncio
async def test_branch_service_get_not_found():
    branch_repo = AsyncMock()
    branch_repo.get_by_id.return_value = None

    service = BranchService(branch_repository=branch_repo)
    with pytest.raises(EntityNotFoundException):
        await service.get_branch(999)
