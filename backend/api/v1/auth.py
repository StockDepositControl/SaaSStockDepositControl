from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.users.models import AuthToken, LoginCredentials, UserRole
from backend.app.ports.security import TokenProvider, PasswordHasher
from backend.api.dependencies import get_token_provider, get_password_hasher

router = APIRouter()

@router.post("/login", response_model=AuthToken)
async def login(
    credentials: LoginCredentials,
    token_provider: TokenProvider = Depends(get_token_provider),
    hasher: PasswordHasher = Depends(get_password_hasher)
):
    """
    Login endpoint that accepts credentials and returns a signed JWT containing 
    the user's role and id_sucursal (tenant_id) as claims.
    """
    # Dummy credentials store for the security skeleton verification
    if credentials.email == "admin@globalmedica.com" and credentials.password == "admin":
        role = UserRole.ADMINISTRADOR
        id_sucursal = 1
    elif credentials.email == "supervisor@globalmedica.com" and credentials.password == "supervisor":
        role = UserRole.SUPERVISOR
        id_sucursal = 1
    elif credentials.email == "auditor@globalmedica.com" and credentials.password == "auditor":
        role = UserRole.AUDITOR
        id_sucursal = 1
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token_data = {
        "sub": credentials.email,
        "role": role.value,
        "id_sucursal": id_sucursal
    }
    
    # Generate and sign the token
    access_token = token_provider.create_token(data=token_data)
    return AuthToken(access_token=access_token, token_type="bearer")
