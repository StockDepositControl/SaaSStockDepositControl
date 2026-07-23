from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from backend.app.ports.database import ConnectionProvider
from backend.api.dependencies import get_connection_provider

router = APIRouter()

@router.get("/health")
async def health_check(connection_provider: ConnectionProvider = Depends(get_connection_provider)) -> JSONResponse:
    """
    Database-backed health check endpoint.
    Probes database connectivity via the ConnectionProvider port.
    Returns 200 OK if online, or 503 Service Unavailable if the probe fails.
    """
    try:
        is_connected = await connection_provider.check_connectivity()

        if is_connected:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "healthy",
                    "database": "connected"
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "database": "disconnected",
                    "detail": "Database connectivity probe failed"
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "detail": str(e)
            }
        )
