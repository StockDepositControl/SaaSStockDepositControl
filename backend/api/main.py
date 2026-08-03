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

# Load environment configuration
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # App startup
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

# Include versioned router to layout future resources cleanly
app.include_router(v1_router)

