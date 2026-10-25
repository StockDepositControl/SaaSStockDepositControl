import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add the parent directory to the python path to resolve 'backend' imports correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from backend.api.v1.health import router as health_router
from backend.api.exception_handlers import register_exception_handlers
from backend.api.dependencies import get_connection_provider
from backend.api.middlewares.tenant_auth import TenantAuthMiddleware
from backend.api.v1.auth import router as auth_router
from backend.api.v1.articles import router as articles_router
from backend.api.v1.stock import router as stock_router
from backend.api.v1.enterprises import router as enterprises_router
from backend.api.v1.branches import router as branches_router
from backend.api.v1.reports import router as reports_router
from backend.api.v1.users import router as users_router

# Load environment configuration
load_dotenv()

logger = logging.getLogger(__name__)

INSECURE_SECRET_KEYS = {"", "changeme", "changeme_secret_key", "secret"}
MIN_SECRET_KEY_LENGTH = 32


def validate_production_secret_key() -> None:
    """Refuse to start in production with a trivial SECRET_KEY (sole authority for this check)."""
    if os.getenv("ENVIRONMENT", "development") != "production":
        return
    secret_key = os.getenv("SECRET_KEY", "")
    if secret_key in INSECURE_SECRET_KEYS or len(secret_key) < MIN_SECRET_KEY_LENGTH:
        logger.critical("CRITICAL: Application refused to start in production with insecure SECRET_KEY")
        raise RuntimeError("Insecure SECRET_KEY configured")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # App startup
    validate_production_secret_key()
    yield
    # App shutdown: dispose of active SQLAlchemy connection pools
    provider = get_connection_provider()
    if hasattr(provider, "dispose"):
        await provider.dispose()

app = FastAPI(
    title="SaaS Stock Deposit Control API",
    description="Backend API for the SaaS Stock Deposit Control system.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
origins_str = os.getenv("CORS_ORIGINS", "*")
origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]

# Regex to permit local development over private LANs (192.168.x.x, 10.x.x.x, 172.16-31.x.x, localhost)
local_network_regex = r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=local_network_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantAuthMiddleware)

# Centralized exception handlers registration
register_exception_handlers(app)

# Base health route (for infrastructure probes)
app.include_router(health_router, tags=["Health"])

# Versioned API routes registration structure
from fastapi import APIRouter
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_router, tags=["Health"])
v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
v1_router.include_router(articles_router, prefix="/articles", tags=["Articles"])
v1_router.include_router(stock_router, prefix="/stock", tags=["Stock & Audit"])
v1_router.include_router(enterprises_router, prefix="/enterprises", tags=["Enterprises"])
v1_router.include_router(branches_router, prefix="/branches", tags=["Branches"])
v1_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
v1_router.include_router(users_router, prefix="/users", tags=["Users"])

# Include versioned router to layout future resources cleanly
app.include_router(v1_router)


