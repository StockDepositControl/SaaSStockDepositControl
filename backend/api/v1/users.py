from typing import List
from fastapi import APIRouter, Depends, Query, status

from backend.api.dependencies.auth import RoleChecker
from backend.api.dependencies.services import get_user_service
from backend.app.users.models import UserResponse, UserStatusUpdate, UserRoleAssignment
from backend.app.users.services import UserService

router = APIRouter()

# Strictly enforce Role-Based Access Control: Administrators only
require_admin = RoleChecker(allowed_roles=["administrador"])


@router.get(
    "",
    response_model=List[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List Organization Users",
    description="Retrieves all users belonging to the administrator's tenant, with optional inclusion of inactive accounts.",
)
async def list_users(
    include_inactive: bool = Query(default=True, description="Whether to include inactive users"),
    claims: dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> List[UserResponse]:
    tenant_id = int(claims.get("tenant_id", 1))
    users = await user_service.list_users(tenant_id=tenant_id, include_inactive=include_inactive)
    return [UserResponse.model_validate(u) for u in users]


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Toggle User Active Status",
    description="Activates or deactivates a user. Prevents administrator self-deactivation.",
)
async def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    claims: dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    tenant_id = int(claims.get("tenant_id", 1))
    actor_id = int(claims.get("id_usuario") or claims.get("user_id", 1))
    user = await user_service.update_status(
        tenant_id=tenant_id,
        target_user_id=user_id,
        is_active=payload.is_active,
        actor_user_id=actor_id,
    )
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}/roles",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign User Roles",
    description="Assigns operational roles to a user. Enforces single-role constraint and prevents administrator self-demotion.",
)
async def assign_user_roles(
    user_id: int,
    payload: UserRoleAssignment,
    claims: dict = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
) -> UserResponse:
    tenant_id = int(claims.get("tenant_id", 1))
    actor_id = int(claims.get("id_usuario") or claims.get("user_id", 1))
    user = await user_service.assign_roles(
        tenant_id=tenant_id,
        target_user_id=user_id,
        roles=payload.roles,
        actor_user_id=actor_id,
    )
    return UserResponse.model_validate(user)
