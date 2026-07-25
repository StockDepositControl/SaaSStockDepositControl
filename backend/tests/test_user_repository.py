import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.adapters.repositories.user_repository import SQLAlchemyUserRepository
from backend.app.users.models import User, UserRole

@pytest.mark.asyncio
async def test_get_by_email_found():
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    mock_usuario = MagicMock()
    mock_usuario.id_usuario = 1
    mock_usuario.tenant_id = "GlobalMedica_01"
    mock_usuario.nombre_completo = "Test User"
    mock_usuario.email = "test@globalmedica.com"
    mock_usuario.rol = UserRole.ADMINISTRADOR
    mock_usuario.id_sucursal = 1
    mock_usuario.is_active = True

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_usuario
    mock_session.execute.return_value = mock_result

    repo = SQLAlchemyUserRepository(mock_session_factory)
    user = await repo.get_by_email(tenant_id="GlobalMedica_01", email="test@globalmedica.com")

    assert user is not None
    assert user.id_usuario == 1
    assert user.email == "test@globalmedica.com"
    assert user.rol == UserRole.ADMINISTRADOR
    assert user.tenant_id == "GlobalMedica_01"

@pytest.mark.asyncio
async def test_get_by_email_not_found():
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    repo = SQLAlchemyUserRepository(mock_session_factory)
    user = await repo.get_by_email(tenant_id="GlobalMedica_01", email="nonexistent@globalmedica.com")

    assert user is None

@pytest.mark.asyncio
async def test_get_password_hash():
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = "$2b$12$hashedpasswordstring"
    mock_session.execute.return_value = mock_result

    repo = SQLAlchemyUserRepository(mock_session_factory)
    hash_val = await repo.get_password_hash(tenant_id="GlobalMedica_01", email="test@globalmedica.com")

    assert hash_val == "$2b$12$hashedpasswordstring"
