from typing import List

from backend.api.dependencies.services import get_branch_service
from backend.app.branches.models import Branch, BranchCreate, BranchUpdate
from backend.app.branches.services import BranchService
from fastapi import APIRouter, Depends, status

router = APIRouter()


@router.get("/{branch_id}", response_model=Branch)
async def get_branch(
    branch_id: int,
    service: BranchService = Depends(get_branch_service),
) -> Branch:
    """Retrieve a branch by id_branch."""
    return await service.get_branch(branch_id)


@router.get("/tenant/{tenant_id}", response_model=List[Branch])
async def list_branches_by_tenant(
    tenant_id: int,
    service: BranchService = Depends(get_branch_service),
) -> List[Branch]:
    """List all branches belonging to a specific enterprise."""
    return await service.list_branches_by_tenant(tenant_id)


@router.post("", response_model=Branch, status_code=status.HTTP_201_CREATED)
async def create_branch(
    data: BranchCreate,
    service: BranchService = Depends(get_branch_service),
) -> Branch:
    """Create a new branch."""
    return await service.create_branch(data)


@router.put("/{branch_id}", response_model=Branch)
async def update_branch(
    branch_id: int,
    data: BranchUpdate,
    service: BranchService = Depends(get_branch_service),
) -> Branch:
    """Update an existing branch."""
    return await service.update_branch(branch_id, data)


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: int,
    service: BranchService = Depends(get_branch_service),
) -> None:
    """Delete a branch."""
    await service.delete_branch(branch_id)
