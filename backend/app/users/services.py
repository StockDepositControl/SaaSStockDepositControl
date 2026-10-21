from typing import Optional, List
from backend.app.users.models import User, AuthToken, UserRole
from backend.app.users.ports import UserRepositoryPort
from backend.app.ports.security import TokenProvider, PasswordHasher
from backend.app.exceptions import EntityNotFoundException, BusinessRuleViolationException

class AuthService:
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        password_hasher: PasswordHasher,
        token_provider: TokenProvider,
        access_token_expire_minutes: int = 480
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_provider = token_provider
        self.access_token_expire_minutes = access_token_expire_minutes

    async def authenticate(self, email: str, password: str) -> AuthToken:
        """
        Authenticates a user by email using password_hasher,
        and returns a signed AuthToken containing JWT claims.
        Rejects inactive user accounts.
        """
        user = await self.user_repository.get_by_email(email=email)
        if not user:
            raise EntityNotFoundException("User not found")

        if not user.is_active:
            raise BusinessRuleViolationException("User account is inactive")

        stored_hash = await self.user_repository.get_password_hash(email=email)
        if not stored_hash or not self.password_hasher.verify(password, stored_hash):
            raise BusinessRuleViolationException("Invalid credentials")

        first_role = user.roles[0] if user.roles else "administrador"
        role_str = first_role.value if hasattr(first_role, "value") else str(first_role)

        token_data = {
            "sub": user.email,
            "role": role_str,
            "tenant_id": user.tenant_id,
            "branch_id": user.branch_id,
            "user_id": user.user_id,
            "id_usuario": user.user_id,
        }

        access_token = self.token_provider.create_token(
            data=token_data,
            expires_delta=self.access_token_expire_minutes
        )

        return AuthToken(access_token=access_token, token_type="bearer")

    async def get_current_user(self, user_id: int, tenant_id: int) -> User:
        """
        Retrieves user domain model by user_id and tenant_id.
        """
        user = await self.user_repository.get_by_id(tenant_id=tenant_id, user_id=user_id)
        if not user:
            raise EntityNotFoundException("User not found")
        return user


class UserService:
    """
    Domain service orchestrating tenant user administration operations:
    listing, activation status toggling, and role assignment.
    """
    def __init__(self, user_repository: UserRepositoryPort):
        self.user_repository = user_repository

    async def list_users(self, tenant_id: int, include_inactive: bool = True) -> List[User]:
        return await self.user_repository.list_by_tenant(tenant_id=tenant_id, include_inactive=include_inactive)

    async def update_status(self, tenant_id: int, target_user_id: int, is_active: bool, actor_user_id: int) -> User:
        if target_user_id == actor_user_id and not is_active:
            raise BusinessRuleViolationException("Administrators cannot deactivate their own account")

        user = await self.user_repository.get_by_id(tenant_id=tenant_id, user_id=target_user_id, include_inactive=True)
        if not user:
            raise EntityNotFoundException(f"User {target_user_id} not found in this tenant")

        return await self.user_repository.update_status(tenant_id=tenant_id, user_id=target_user_id, is_active=is_active)

    async def assign_roles(self, tenant_id: int, target_user_id: int, roles: List[UserRole], actor_user_id: int) -> User:
        if not roles:
            raise BusinessRuleViolationException("A user must have at least one role assigned")
        if len(roles) != 1:
            raise BusinessRuleViolationException("A user can only have one role at a time")

        user = await self.user_repository.get_by_id(tenant_id=tenant_id, user_id=target_user_id, include_inactive=True)
        if not user:
            raise EntityNotFoundException(f"User {target_user_id} not found in this tenant")

        if target_user_id == actor_user_id and UserRole.ADMINISTRADOR not in roles:
            raise BusinessRuleViolationException("Administrators cannot remove the administrator role from themselves")

        return await self.user_repository.update_roles(tenant_id=tenant_id, user_id=target_user_id, roles=roles)
