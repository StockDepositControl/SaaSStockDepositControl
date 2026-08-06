import pytest
from unittest.mock import AsyncMock
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.api.dependencies import get_token_provider
from backend.api.dependencies.auth import get_current_user_claims, RoleChecker
from backend.api.dependencies.services import get_auth_service
from backend.adapters.security.jwt_provider import PyJWTTokenProvider
from backend.app.users.models import AuthToken
from backend.app.exceptions import BusinessRuleViolationException

# Add a test router for authentication/authorization dependency verification
test_router = APIRouter(prefix="/api/v1/test")

@test_router.get("/protected")
def protected_route(claims: dict = Depends(get_current_user_claims)):
    return {"status": "authenticated", "claims": claims}

@test_router.get("/admin-only")
def admin_only_route(claims: dict = Depends(RoleChecker(["administrador"]))):
    return {"status": "admin_access"}

# Integrate test routes into main app instance
app.include_router(test_router)

client = TestClient(app)

@pytest.fixture
def test_token_provider():
    # Use a predictable key for verifying claims
    return PyJWTTokenProvider(secret_key="test-secret-key-that-is-long-enough-for-hs256")

def test_login_success_and_token_emission(test_token_provider):
    mock_auth_service = AsyncMock()
    signed_token = test_token_provider.create_token(data={
        "sub": "admin@globalmedica.com",
        "role": "administrador",
        "tenant_id": "GlobalMedica_01",
        "branch_id": 1,
        "user_id": 1,
        "id_usuario": 1,
    })
    mock_auth_service.authenticate.return_value = AuthToken(access_token=signed_token, token_type="bearer")

    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_token_provider] = lambda: test_token_provider

    response = client.post("/api/v1/auth/login", json={
        "tenant_id": "GlobalMedica_01",
        "email": "admin@globalmedica.com",
        "password": "admin"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Decode and verify the claims
    claims = test_token_provider.decode_token(data["access_token"])
    assert claims["role"] == "administrador"
    assert claims["tenant_id"] == "GlobalMedica_01"
    assert claims["branch_id"] == 1

    app.dependency_overrides.clear()

def test_login_invalid_credentials():
    mock_auth_service = AsyncMock()
    mock_auth_service.authenticate.side_effect = BusinessRuleViolationException("Invalid credentials")

    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    response = client.post("/api/v1/auth/login", json={
        "tenant_id": "GlobalMedica_01",
        "email": "admin@globalmedica.com",
        "password": "wrong_password"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid credentials"

    app.dependency_overrides.clear()

def test_request_with_valid_token(test_token_provider):
    app.dependency_overrides[get_token_provider] = lambda: test_token_provider

    token = test_token_provider.create_token(data={"sub": "user@test.com", "role": "supervisor", "branch_id": 1})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/test/protected", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "authenticated"

    app.dependency_overrides.clear()

def test_request_with_invalid_or_expired_token(test_token_provider):
    app.dependency_overrides[get_token_provider] = lambda: test_token_provider

    # Invalid token signature
    headers = {"Authorization": "Bearer invalid.token.payload"}
    response = client.get("/api/v1/test/protected", headers=headers)
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]

    # Expired token
    expired_token = test_token_provider.create_token(data={"sub": "user@test.com"}, expires_delta=-1)
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/test/protected", headers=headers)
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]

    app.dependency_overrides.clear()

def test_request_with_insufficient_privileges(test_token_provider):
    app.dependency_overrides[get_token_provider] = lambda: test_token_provider

    # A supervisor attempting to access admin-only route
    token = test_token_provider.create_token(data={"sub": "user@test.com", "role": "supervisor", "branch_id": 1})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/api/v1/test/admin-only", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Operation not permitted for this role"

    # Admin accessing admin-only route
    admin_token = test_token_provider.create_token(data={"sub": "user@test.com", "role": "administrador", "branch_id": 1})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = client.get("/api/v1/test/admin-only", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "admin_access"

    app.dependency_overrides.clear()
