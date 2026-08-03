from fastapi import APIRouter, Depends
from backend.app.users.models import AuthToken, LoginCredentials
from backend.app.users.services import AuthService
from backend.api.dependencies.services import get_auth_service

router = APIRouter()

@router.post("/login", response_model=AuthToken)
async def login(
    credentials: LoginCredentials,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthToken:
    """
    Login endpoint that verifies user credentials against the database
    and returns a signed JWT token with user claims.
    """
    return await auth_service.authenticate(
        email=credentials.email,
        password=credentials.password
    )
