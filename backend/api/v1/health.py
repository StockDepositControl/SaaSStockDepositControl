from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from backend.app.ports.database import ConnectionProvider
from backend.api.dependencies import get_connection_provider

router = APIRouter()

@router.get("/health")
async def health_check(connection_provider: ConnectionProvider = Depends(get_connection_provider)) -> JSONResponse:
    """
    Database-backed health check endpoint.
    Queries the database via the connection provider port using 'SELECT 1'.
    Returns 200 OK if online, or 503 Service Unavailable if the query fails.
    """
    try:
        async with connection_provider.session() as session:
            raw = session.raw_session
            await raw.execute(text("SELECT 1"))
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "database": "connected"
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
