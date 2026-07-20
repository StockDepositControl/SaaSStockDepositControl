from abc import ABC, abstractmethod
from typing import Any, Dict

class TokenProvider(ABC):
    @abstractmethod
    def create_token(self, data: Dict[str, Any], expires_delta: int = None) -> str:
        """
        Create and sign a JWT token.
        """
        pass

    @abstractmethod
    def decode_token(self, token: str) -> Dict[str, Any]:
        """
        Decode and verify a JWT token. Raises ValueError on failure.
        """
        pass

class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        """
        Hash a plain text password.
        """
        pass

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed one.
        """
        pass
