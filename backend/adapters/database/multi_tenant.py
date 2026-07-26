import contextvars
from typing import Optional

# Async ContextVars for request-scoped tenant isolation and user context
tenant_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)
sucursal_id_context: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("sucursal_id", default=None)
user_id_context: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("user_id", default=None)

def get_tenant_id() -> Optional[str]:
    """Returns the current request's tenant_id bound to the async ContextVar."""
    return tenant_id_context.get()

def set_tenant_id(tenant_id: Optional[str]) -> None:
    """Binds tenant_id to the current async request ContextVar."""
    tenant_id_context.set(tenant_id)

def get_sucursal_id() -> Optional[int]:
    """Returns the current request's sucursal_id bound to the async ContextVar."""
    return sucursal_id_context.get()

def set_sucursal_id(sucursal_id: Optional[int]) -> None:
    """Binds sucursal_id to the current async request ContextVar."""
    sucursal_id_context.set(sucursal_id)

def get_user_id() -> Optional[int]:
    """Returns the current request's user_id bound to the async ContextVar."""
    return user_id_context.get()

def set_user_id(user_id: Optional[int]) -> None:
    """Binds user_id to the current async request ContextVar."""
    user_id_context.set(user_id)
