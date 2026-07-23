from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.users.models import AuthToken, LoginCredentials, UserRole
from backend.app.ports.security import TokenProvider
from backend.api.dependencies import get_token_provider

router = APIRouter()

@router.post("/login", response_model=AuthToken)
async def login(
    credentials: LoginCredentials,
    token_provider: TokenProvider = Depends(get_token_provider),
):
    """
    Login endpoint that accepts credentials and returns a signed JWT containing
    the user's role, tenant_id, and id_sucursal as claims.
    """
    # Dummy credentials store for the security skeleton verification.
    # Will be replaced by UserRepositoryPort lookup when wired.
    if credentials.email == "admin@globalmedica.com" and credentials.password == "admin":
        role = UserRole.ADMINISTRADOR
        tenant_id = "GlobalMedica_01"
        id_sucursal = 1
    elif credentials.email == "supervisor@globalmedica.com" and credentials.password == "supervisor":
        role = UserRole.SUPERVISOR
        tenant_id = "GlobalMedica_01"
        id_sucursal = 1
    elif credentials.email == "auditor@globalmedica.com" and credentials.password == "auditor":
        role = UserRole.AUDITOR
        tenant_id = "GlobalMedica_01"
        id_sucursal = 1
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token_data = {
        "sub": credentials.email,
        "role": role.value,
        "tenant_id": tenant_id,
        "id_sucursal": id_sucursal
    }

    # Generate and sign the token
    access_token = token_provider.create_token(data=token_data)
    return AuthToken(access_token=access_token, token_type="bearer")
