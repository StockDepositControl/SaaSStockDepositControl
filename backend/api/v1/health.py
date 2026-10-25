import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from backend.app.ports.database import LOGICAL_DATABASES, ConnectionProvider
from backend.api.dependencies import get_connection_provider

router = APIRouter()
logger = logging.getLogger(__name__)

_PROBE_FAILED_DETAIL = "Database connectivity probe failed"


def _label(is_connected: bool) -> str:
    return "connected" if is_connected else "disconnected"


@router.get("/health")
async def health_check(
    request: Request,
    connection_provider: ConnectionProvider = Depends(get_connection_provider),
) -> JSONResponse:
    """
    Database-backed health check endpoint.
    Probes every logical database (articles, users, analytics) via the ConnectionProvider port.
    Returns 200 OK only if all are online, or 503 Service Unavailable otherwise.
    The legacy "database" key is kept as the aggregate status for existing probes.
    """
    version = request.app.version
    try:
        results = await connection_provider.check_databases()
    except Exception:
        logger.exception("Health probe raised an unexpected error")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "databases": {name: "disconnected" for name in LOGICAL_DATABASES},
                "version": version,
                "detail": _PROBE_FAILED_DETAIL,
            },
        )

    statuses = {name: results.get(name, False) for name in LOGICAL_DATABASES}
    all_connected = all(statuses.values())
    databases = {name: _label(is_connected) for name, is_connected in statuses.items()}
    content = {
        "status": "healthy" if all_connected else "unhealthy",
        "database": _label(all_connected),
        "databases": databases,
        "version": version,
    }
    if not all_connected:
        content["detail"] = _PROBE_FAILED_DETAIL
    return JSONResponse(
        status_code=status.HTTP_200_OK if all_connected else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=content,
    )
