from typing import Optional
from backend.app.users.models import User, AuthToken
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
        """
        user = await self.user_repository.get_by_email(email=email)
        if not user:
            raise EntityNotFoundException("User not found")

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
