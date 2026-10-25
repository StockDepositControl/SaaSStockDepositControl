from abc import ABC, abstractmethod
from typing import List, Optional

from backend.app.users.models import User, UserRole


class UserRepositoryPort(ABC):
    @abstractmethod
    async def get_by_email(
        self, email: str, tenant_id: Optional[int] = None
    ) -> Optional[User]:
        """
        Retrieve a domain User by email, optionally filtered by tenant_id.
        """
        pass

    @abstractmethod
    async def get_by_id(
        self, tenant_id: int, user_id: int, include_inactive: bool = True
    ) -> Optional[User]:
        """
        Retrieve a domain User by tenant_id and user_id, optionally including inactive
        users.
        """
        pass

    @abstractmethod
    async def get_password_hash(
        self, email: str, tenant_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Retrieve the stored password hash for a given email.
        """
        pass

    @abstractmethod
    async def list_by_tenant(
        self, tenant_id: int, include_inactive: bool = True
    ) -> List[User]:
        """
        Retrieve all domain Users belonging to a tenant.
        """
        pass

    @abstractmethod
    async def update_status(
        self, tenant_id: int, user_id: int, is_active: bool
    ) -> User:
        """
        Update the is_active status of a user within a tenant.
        """
        pass

    @abstractmethod
    async def update_roles(
        self, tenant_id: int, user_id: int, roles: List[UserRole]
    ) -> User:
        """
        Update the assigned roles of a user within a tenant.
        """
        pass
