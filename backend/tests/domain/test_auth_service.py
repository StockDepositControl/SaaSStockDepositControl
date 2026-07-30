import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.users.services import AuthService
from backend.app.users.models import User, UserRole, AuthToken
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException

@pytest.mark.asyncio
async def test_authenticate_success():
    mock_repo = AsyncMock()
    mock_hasher = MagicMock()
    mock_token_provider = MagicMock()

    dummy_user = User(
        id_usuario=10,
        tenant_id="Tenant1",
        nombre_completo="Juan Perez",
        email="juan@tenant1.com",
        rol=UserRole.SUPERVISOR,
        id_sucursal=2
    )

    mock_repo.get_by_email.return_value = dummy_user
    mock_repo.get_password_hash.return_value = "$2b$12$hashed"
    mock_hasher.verify.return_value = True
    mock_token_provider.create_token.return_value = "mocked.jwt.token"

    auth_service = AuthService(
        user_repository=mock_repo,
        password_hasher=mock_hasher,
        token_provider=mock_token_provider,
        access_token_expire_minutes=60
    )

    result = await auth_service.authenticate("juan@tenant1.com", "secret123", "Tenant1")

    assert isinstance(result, AuthToken)
    assert result.access_token == "mocked.jwt.token"
    assert result.token_type == "bearer"

    mock_repo.get_by_email.assert_called_once_with(tenant_id="Tenant1", email="juan@tenant1.com")
    mock_hasher.verify.assert_called_once_with("secret123", "$2b$12$hashed")
    mock_token_provider.create_token.assert_called_once()
    
    token_payload = mock_token_provider.create_token.call_args[1]["data"]
    assert token_payload["sub"] == "juan@tenant1.com"
    assert token_payload["role"] == "supervisor"
    assert token_payload["tenant_id"] == "Tenant1"
    assert token_payload["id_sucursal"] == 2
    assert token_payload["id_usuario"] == 10

@pytest.mark.asyncio
async def test_authenticate_user_not_found():
    mock_repo = AsyncMock()
    mock_hasher = MagicMock()
    mock_token_provider = MagicMock()

    mock_repo.get_by_email.return_value = None

    auth_service = AuthService(
        user_repository=mock_repo,
        password_hasher=mock_hasher,
        token_provider=mock_token_provider
    )

    with pytest.raises(EntityNotFoundException) as exc_info:
        await auth_service.authenticate("unknown@tenant1.com", "secret", "Tenant1")

    assert "User not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_authenticate_invalid_password():
    mock_repo = AsyncMock()
    mock_hasher = MagicMock()
    mock_token_provider = MagicMock()

    dummy_user = User(
        id_usuario=1,
        tenant_id="Tenant1",
        nombre_completo="User",
        email="user@tenant.com",
        rol=UserRole.AUDITOR,
        id_sucursal=1
    )

    mock_repo.get_by_email.return_value = dummy_user
    mock_repo.get_password_hash.return_value = "$2b$12$hashed"
    mock_hasher.verify.return_value = False

    auth_service = AuthService(
        user_repository=mock_repo,
        password_hasher=mock_hasher,
        token_provider=mock_token_provider
    )

    with pytest.raises(BusinessRuleViolationException) as exc_info:
        await auth_service.authenticate("user@tenant.com", "wrong_password", "Tenant1")

    assert "Invalid credentials" in str(exc_info.value)
