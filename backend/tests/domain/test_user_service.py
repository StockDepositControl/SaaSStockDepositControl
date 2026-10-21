import pytest
from unittest.mock import AsyncMock
from backend.app.users.services import UserService
from backend.app.users.models import User, UserRole
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException

@pytest.fixture
def mock_user_repo():
    return AsyncMock()

@pytest.fixture
def user_service(mock_user_repo):
    return UserService(user_repository=mock_user_repo)

def create_sample_user(user_id=1, tenant_id=1, email="admin@tenant.com", is_active=True, roles=None):
    return User(
        user_id=user_id,
        tenant_id=tenant_id,
        first_name="Test",
        last_name="User",
        email=email,
        roles=roles if roles is not None else [UserRole.ADMINISTRADOR],
        branch_id=1,
        is_active=is_active
    )

@pytest.mark.asyncio
async def test_list_users(user_service, mock_user_repo):
    expected_users = [create_sample_user(1), create_sample_user(2, email="auditor@tenant.com")]
    mock_user_repo.list_by_tenant.return_value = expected_users

    result = await user_service.list_users(tenant_id=1, include_inactive=True)

    assert result == expected_users
    mock_user_repo.list_by_tenant.assert_called_once_with(tenant_id=1, include_inactive=True)

@pytest.mark.asyncio
async def test_update_status_success(user_service, mock_user_repo):
    target_user = create_sample_user(user_id=2, email="auditor@tenant.com", is_active=True)
    updated_user = create_sample_user(user_id=2, email="auditor@tenant.com", is_active=False)

    mock_user_repo.get_by_id.return_value = target_user
    mock_user_repo.update_status.return_value = updated_user

    result = await user_service.update_status(tenant_id=1, target_user_id=2, is_active=False, actor_user_id=1)

    assert result.is_active is False
    mock_user_repo.get_by_id.assert_called_once_with(tenant_id=1, user_id=2, include_inactive=True)
    mock_user_repo.update_status.assert_called_once_with(tenant_id=1, user_id=2, is_active=False)

@pytest.mark.asyncio
async def test_update_status_self_deactivation_raises_exception(user_service, mock_user_repo):
    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await user_service.update_status(tenant_id=1, target_user_id=1, is_active=False, actor_user_id=1)

    assert "Administrators cannot deactivate their own account" in str(exc_info.value)
    mock_user_repo.get_by_id.assert_not_called()
    mock_user_repo.update_status.assert_not_called()

@pytest.mark.asyncio
async def test_update_status_user_not_found(user_service, mock_user_repo):
    mock_user_repo.get_by_id.return_value = None

    with pytest.raises(EntityNotFoundException) as exc_info:
        await user_service.update_status(tenant_id=1, target_user_id=999, is_active=False, actor_user_id=1)

    assert "User 999 not found" in str(exc_info.value)
    mock_user_repo.update_status.assert_not_called()

@pytest.mark.asyncio
async def test_assign_roles_success(user_service, mock_user_repo):
    target_user = create_sample_user(user_id=2, roles=[UserRole.AUDITOR])
    updated_user = create_sample_user(user_id=2, roles=[UserRole.SUPERVISOR])

    mock_user_repo.get_by_id.return_value = target_user
    mock_user_repo.update_roles.return_value = updated_user

    result = await user_service.assign_roles(
        tenant_id=1,
        target_user_id=2,
        roles=[UserRole.SUPERVISOR],
        actor_user_id=1
    )

    assert result.roles == [UserRole.SUPERVISOR]
    mock_user_repo.update_roles.assert_called_once_with(tenant_id=1, user_id=2, roles=[UserRole.SUPERVISOR])

@pytest.mark.asyncio
async def test_assign_roles_empty_roles_raises_exception(user_service):
    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await user_service.assign_roles(tenant_id=1, target_user_id=2, roles=[], actor_user_id=1)

    assert "A user must have at least one role assigned" in str(exc_info.value)

@pytest.mark.asyncio
async def test_assign_roles_multiple_roles_raises_exception(user_service):
    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await user_service.assign_roles(
            tenant_id=1,
            target_user_id=2,
            roles=[UserRole.SUPERVISOR, UserRole.AUDITOR],
            actor_user_id=1
        )

    assert "A user can only have one role at a time" in str(exc_info.value)

@pytest.mark.asyncio
async def test_assign_roles_self_demotion_raises_exception(user_service, mock_user_repo):
    admin_user = create_sample_user(user_id=1, roles=[UserRole.ADMINISTRADOR])
    mock_user_repo.get_by_id.return_value = admin_user

    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await user_service.assign_roles(
            tenant_id=1,
            target_user_id=1,
            roles=[UserRole.SUPERVISOR],
            actor_user_id=1
        )

    assert "Administrators cannot remove the administrator role from themselves" in str(exc_info.value)
    mock_user_repo.update_roles.assert_not_called()
