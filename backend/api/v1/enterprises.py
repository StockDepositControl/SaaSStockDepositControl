from typing import List
from fastapi import APIRouter, Depends, status

from backend.app.enterprises.models import Enterprise, EnterpriseCreate, EnterpriseUpdate
from backend.app.enterprises.services import EnterpriseService
from backend.api.dependencies.services import get_enterprise_service

router = APIRouter()

@router.get("", response_model=List[Enterprise])
async def list_enterprises(
    service: EnterpriseService = Depends(get_enterprise_service),
) -> List[Enterprise]:
    """Retrieve all enterprises."""
    return await service.list_enterprises()


@router.get("/{tenant_id}", response_model=Enterprise)
async def get_enterprise(
    tenant_id: int,
    service: EnterpriseService = Depends(get_enterprise_service),
) -> Enterprise:
    """Retrieve an enterprise by tenant_id."""
    return await service.get_enterprise(tenant_id)


@router.post("", response_model=Enterprise, status_code=status.HTTP_201_CREATED)
async def create_enterprise(
    data: EnterpriseCreate,
    service: EnterpriseService = Depends(get_enterprise_service),
) -> Enterprise:
    """Create a new enterprise."""
    return await service.create_enterprise(data)


@router.put("/{tenant_id}", response_model=Enterprise)
async def update_enterprise(
    tenant_id: int,
    data: EnterpriseUpdate,
    service: EnterpriseService = Depends(get_enterprise_service),
) -> Enterprise:
    """Update an existing enterprise."""
    return await service.update_enterprise(tenant_id, data)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_enterprise(
    tenant_id: int,
    service: EnterpriseService = Depends(get_enterprise_service),
) -> None:
    """Delete an enterprise."""
    await service.delete_enterprise(tenant_id)
