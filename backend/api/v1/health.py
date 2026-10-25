from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from backend.app.ports.database import ConnectionProvider
from backend.api.dependencies import get_connection_provider

router = APIRouter()

_DATABASES = ("articles", "users", "analytics")


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
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "databases": {name: "disconnected" for name in _DATABASES},
                "version": version,
                "detail": str(e),
            },
        )

    databases = {name: _label(results.get(name, False)) for name in _DATABASES}
    all_connected = all(value == "connected" for value in databases.values())
    content = {
        "status": "healthy" if all_connected else "unhealthy",
        "database": _label(all_connected),
        "databases": databases,
        "version": version,
    }
    if not all_connected:
        content["detail"] = "Database connectivity probe failed"
    return JSONResponse(
        status_code=status.HTTP_200_OK if all_connected else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=content,
    )
