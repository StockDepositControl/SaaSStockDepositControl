import contextvars
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from backend.api.dependencies import get_token_provider

# Global context var to bind the resolved tenant ID to the active async context
tenant_id_context: contextvars.ContextVar[int | None] = contextvars.ContextVar("tenant_id", default=None)

class TenantAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                provider = get_token_provider()
                payload = provider.decode_token(token)
                tenant_id = payload.get("id_sucursal")
                if tenant_id is not None:
                    tenant_id_context.set(int(tenant_id))
            except ValueError:
                # Invalid or expired token; downstream authentication dependencies will reject it
                pass

        response = await call_next(request)
        return response
