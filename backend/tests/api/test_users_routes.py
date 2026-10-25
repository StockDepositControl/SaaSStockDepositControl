from unittest.mock import AsyncMock

import pytest
from backend.api.dependencies.auth import get_current_user_claims
from backend.api.dependencies.services import get_user_service
from backend.api.main import app
from backend.app.exceptions import (
    BusinessRuleViolationException,
    EntityNotFoundException,
)
from backend.app.users.models import User, UserRole
from backend.app.users.services import UserService
from fastapi import status
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_service():
    return AsyncMock(spec=UserService)


@pytest.fixture
def client():
    return TestClient(app)


def test_users_unauthenticated(client):
    response = client.get("/api/v1/users")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_users_forbidden_for_supervisor(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "supervisor@tenant.com",
        "role": "supervisor",
        "tenant_id": 1,
        "id_usuario": 2,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    response = client.get("/api/v1/users")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "not permitted" in response.json()["detail"].lower()


def test_users_forbidden_for_auditor(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "auditor@tenant.com",
        "role": "auditor",
        "tenant_id": 1,
        "id_usuario": 3,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    response = client.get("/api/v1/users")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_users_as_admin(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@tenant.com",
        "role": "administrador",
        "tenant_id": 1,
        "id_usuario": 1,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    dummy_users = [
        User(
            user_id=1,
            tenant_id=1,
            first_name="Admin",
            last_name="Master",
            email="admin@tenant.com",
            roles=[UserRole.ADMINISTRADOR],
            branch_id=1,
            is_active=True,
        ),
        User(
            user_id=2,
            tenant_id=1,
            first_name="Operator",
            last_name="Worker",
            email="worker@tenant.com",
            roles=[UserRole.AUDITOR],
            branch_id=2,
            is_active=False,
        ),
    ]
    mock_user_service.list_users.return_value = dummy_users

    response = client.get("/api/v1/users?include_inactive=true")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2
    assert data[0]["user_id"] == 1
    assert data[0]["roles"] == ["administrador"]
    assert data[1]["user_id"] == 2
    assert data[1]["is_active"] is False
    assert "password_hash" not in data[0]

    mock_user_service.list_users.assert_called_once_with(
        tenant_id=1, include_inactive=True
    )


def test_update_user_status_success(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@tenant.com",
        "role": "administrador",
        "tenant_id": 1,
        "id_usuario": 1,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    updated_user = User(
        user_id=2,
        tenant_id=1,
        first_name="Operator",
        last_name="Worker",
        email="worker@tenant.com",
        roles=[UserRole.AUDITOR],
        branch_id=2,
        is_active=False,
    )
    mock_user_service.update_status.return_value = updated_user

    response = client.patch("/api/v1/users/2/status", json={"is_active": False})
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["user_id"] == 2
    assert data["is_active"] is False

    mock_user_service.update_status.assert_called_once_with(
        tenant_id=1, target_user_id=2, is_active=False, actor_user_id=1
    )


def test_update_user_status_self_deactivation_forbidden(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@tenant.com",
        "role": "administrador",
        "tenant_id": 1,
        "id_usuario": 1,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    mock_user_service.update_status.side_effect = BusinessRuleViolationException(
        "Administrators cannot deactivate their own account"
    )

    response = client.patch("/api/v1/users/1/status", json={"is_active": False})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cannot deactivate their own account" in response.json()["detail"]


def test_update_user_status_not_found(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@tenant.com",
        "role": "administrador",
        "tenant_id": 1,
        "id_usuario": 1,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    mock_user_service.update_status.side_effect = EntityNotFoundException(
        "User 999 not found"
    )

    response = client.patch("/api/v1/users/999/status", json={"is_active": True})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_assign_user_roles_success(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@tenant.com",
        "role": "administrador",
        "tenant_id": 1,
        "id_usuario": 1,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    updated_user = User(
        user_id=2,
        tenant_id=1,
        first_name="Operator",
        last_name="Worker",
        email="worker@tenant.com",
        roles=[UserRole.SUPERVISOR],
        branch_id=2,
        is_active=True,
    )
    mock_user_service.assign_roles.return_value = updated_user

    response = client.put("/api/v1/users/2/roles", json={"roles": ["supervisor"]})
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["roles"] == ["supervisor"]
    mock_user_service.assign_roles.assert_called_once_with(
        tenant_id=1, target_user_id=2, roles=[UserRole.SUPERVISOR], actor_user_id=1
    )


def test_assign_user_roles_empty_roles(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@tenant.com",
        "role": "administrador",
        "tenant_id": 1,
        "id_usuario": 1,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    mock_user_service.assign_roles.side_effect = BusinessRuleViolationException(
        "A user must have at least one role assigned"
    )

    response = client.put("/api/v1/users/2/roles", json={"roles": []})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "at least one role" in response.json()["detail"]


def test_assign_user_roles_multiple_roles_forbidden(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@tenant.com",
        "role": "administrador",
        "tenant_id": 1,
        "id_usuario": 1,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    mock_user_service.assign_roles.side_effect = BusinessRuleViolationException(
        "A user can only have one role at a time"
    )

    response = client.put(
        "/api/v1/users/2/roles", json={"roles": ["supervisor", "auditor"]}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "one role at a time" in response.json()["detail"]


def test_assign_user_roles_self_demotion_forbidden(client, mock_user_service):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@tenant.com",
        "role": "administrador",
        "tenant_id": 1,
        "id_usuario": 1,
    }
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    mock_user_service.assign_roles.side_effect = BusinessRuleViolationException(
        "Administrators cannot remove the administrator role from themselves"
    )

    response = client.put("/api/v1/users/1/roles", json={"roles": ["supervisor"]})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "cannot remove the administrator role from themselves"
        in response.json()["detail"]
    )


def test_assign_user_roles_invalid_role_enum(client):
    app.dependency_overrides[get_current_user_claims] = lambda: {
        "sub": "admin@tenant.com",
        "role": "administrador",
        "tenant_id": 1,
        "id_usuario": 1,
    }

    response = client.put(
        "/api/v1/users/2/roles", json={"roles": ["super_admin_invalid"]}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
