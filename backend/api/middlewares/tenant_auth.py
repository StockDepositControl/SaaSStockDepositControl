from backend.adapters.database.multi_tenant import (
    set_sucursal_id,
    set_tenant_id,
    set_user_id,
)
from backend.api.dependencies import get_token_provider
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class TenantAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                provider = get_token_provider()
                # Decode and verify the signed token
                payload = provider.decode_token(token)

                tenant_id = payload.get("tenant_id")
                if tenant_id is not None:
                    try:
                        set_tenant_id(int(tenant_id))
                    except (ValueError, TypeError):
                        pass

                branch_id = payload.get("branch_id")
                if branch_id is not None:
                    set_sucursal_id(int(branch_id))
                elif tenant_id is not None:
                    try:
                        set_sucursal_id(int(tenant_id))
                    except (ValueError, TypeError):
                        pass

                user_id = payload.get("user_id")
                if user_id is not None:
                    set_user_id(int(user_id))
            except ValueError:
                # Invalid or expired token; downstream authentication dependencies will
                # reject it
                pass

        response = await call_next(request)
        return response
