from unittest.mock import AsyncMock, MagicMock

import pytest
from backend.adapters.repositories.user_repository import SQLAlchemyUserRepository
from backend.app.users.models import UserRole


@pytest.mark.asyncio
async def test_get_by_email_found():
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    mock_role = MagicMock()
    mock_role.name = "administrador"

    mock_usuario = MagicMock()
    mock_usuario.user_id = 1
    mock_usuario.tenant_id = 1
    mock_usuario.first_name = "Test"
    mock_usuario.last_name = "User"
    mock_usuario.email = "test@globalmedica.com"
    mock_usuario.roles = [mock_role]
    mock_usuario.branch_id = 1
    mock_usuario.is_active = True

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_usuario
    mock_session.execute.return_value = mock_result

    repo = SQLAlchemyUserRepository(mock_session_factory)
    user = await repo.get_by_email(email="test@globalmedica.com")

    assert user is not None
    assert user.user_id == 1
    assert user.email == "test@globalmedica.com"
    assert user.roles == [UserRole.ADMINISTRADOR]
    assert user.tenant_id == 1


@pytest.mark.asyncio
async def test_get_by_email_not_found():
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    repo = SQLAlchemyUserRepository(mock_session_factory)
    user = await repo.get_by_email(email="nonexistent@globalmedica.com")

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
    hash_val = await repo.get_password_hash(email="test@globalmedica.com")

    assert hash_val == "$2b$12$hashedpasswordstring"


@pytest.mark.asyncio
async def test_get_by_id():
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    mock_role = MagicMock()
    mock_role.name = "auditor"

    mock_usuario = MagicMock()
    mock_usuario.user_id = 5
    mock_usuario.tenant_id = 1
    mock_usuario.first_name = "Auditor"
    mock_usuario.last_name = "User"
    mock_usuario.email = "auditor@globalmedica.com"
    mock_usuario.roles = [mock_role]
    mock_usuario.branch_id = 2
    mock_usuario.is_active = True

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_usuario
    mock_session.execute.return_value = mock_result

    repo = SQLAlchemyUserRepository(mock_session_factory)
    user = await repo.get_by_id(tenant_id=1, user_id=5)

    assert user is not None
    assert user.user_id == 5
    assert user.roles == [UserRole.AUDITOR]


@pytest.mark.asyncio
async def test_list_by_tenant():
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    mock_role = MagicMock()
    mock_role.name = "administrador"

    mock_user_1 = MagicMock(
        user_id=1,
        tenant_id=1,
        first_name="A",
        last_name="B",
        email="a@b.com",
        roles=[mock_role],
        branch_id=1,
        is_active=True,
    )
    mock_user_2 = MagicMock(
        user_id=2,
        tenant_id=1,
        first_name="C",
        last_name="D",
        email="c@d.com",
        roles=[],
        branch_id=1,
        is_active=False,
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_user_1, mock_user_2]
    mock_session.execute.return_value = mock_result

    repo = SQLAlchemyUserRepository(mock_session_factory)
    users = await repo.list_by_tenant(tenant_id=1, include_inactive=True)

    assert len(users) == 2
    assert users[0].user_id == 1
    assert users[1].user_id == 2


@pytest.mark.asyncio
async def test_update_status():
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    mock_usuario = MagicMock(
        user_id=1,
        tenant_id=1,
        first_name="A",
        last_name="B",
        email="a@b.com",
        roles=[],
        branch_id=1,
        is_active=True,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_usuario
    mock_session.execute.return_value = mock_result

    repo = SQLAlchemyUserRepository(mock_session_factory)
    updated = await repo.update_status(tenant_id=1, user_id=1, is_active=False)

    assert updated.is_active is False
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_roles():
    mock_session = AsyncMock()
    mock_session_factory = MagicMock(return_value=mock_session)
    mock_session.__aenter__.return_value = mock_session

    mock_usuario = MagicMock(
        user_id=1,
        tenant_id=1,
        first_name="A",
        last_name="B",
        email="a@b.com",
        roles=[],
        branch_id=1,
        is_active=True,
    )
    mock_new_role = MagicMock()
    mock_new_role.name = "supervisor"

    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = mock_usuario

    roles_result = MagicMock()
    roles_result.scalars.return_value.all.return_value = [mock_new_role]

    mock_session.execute.side_effect = [user_result, roles_result]

    repo = SQLAlchemyUserRepository(mock_session_factory)
    updated = await repo.update_roles(
        tenant_id=1, user_id=1, roles=[UserRole.SUPERVISOR]
    )

    assert updated.roles == [UserRole.SUPERVISOR]
    mock_session.commit.assert_awaited_once()
