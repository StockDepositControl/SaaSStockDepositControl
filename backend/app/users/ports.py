from abc import ABC, abstractmethod
from typing import Optional
from backend.app.users.models import User

class UserRepositoryPort(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a domain User by email.
        """
        pass

    @abstractmethod
    async def get_by_id(self, tenant_id: str, id_usuario: int) -> Optional[User]:
        """
        Retrieve a domain User by tenant_id and id_usuario.
        """
        pass

    @abstractmethod
    async def get_password_hash(self, email: str) -> Optional[str]:
        """
        Retrieve the stored password hash for a given email.
        """
        pass
