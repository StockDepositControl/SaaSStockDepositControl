from typing import List

from backend.api.dependencies import get_token_provider
from backend.app.ports.security import TokenProvider
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user_claims(
    token: str = Depends(oauth2_scheme),
    token_provider: TokenProvider = Depends(get_token_provider),
) -> dict:
    """
    FastAPI dependency to extract, decode and verify the JWT.
    Returns the decoded token claims.
    """
    try:
        # Decode and verify the incoming signed token
        payload = token_provider.decode_token(token)
        return payload
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


class RoleChecker:
    """
    Dynamic dependency to check if the verified user has one of the allowed roles.
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, claims: dict = Depends(get_current_user_claims)) -> dict:
        user_role = claims.get("role")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for this role",
            )
        return claims
