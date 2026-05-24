"""
FreelanceRadar — FastAPI Application Entry Point
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import create_tables
from app.routers.auth import router as auth_router
from app.routers.cv import router as cv_router
from app.routers.jobs import router as jobs_router
from app.routers import (
    matches_router,
    cover_letters_router,
    proposals_router,
    alerts_router,
)

logger = structlog.get_logger()

# ── Rate Limiter ─────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("FreelanceRadar API starting", version=settings.APP_VERSION)

    if settings.DEBUG:
        await create_tables()
        logger.info("Database tables ensured (dev mode)")

    yield

    logger.info("FreelanceRadar API shutting down")


# ── App Factory ───────────────────────────────────────────
app = FastAPI(
    title="FreelanceRadar API",
    description="AI-Powered Upwork Intelligence Engine",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Static Files (uploads) ────────────────────────────────
import os
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ── Routers ───────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(cv_router, prefix=API_PREFIX)
app.include_router(jobs_router, prefix=API_PREFIX)
app.include_router(matches_router, prefix=API_PREFIX)
app.include_router(cover_letters_router, prefix=API_PREFIX)
app.include_router(proposals_router, prefix=API_PREFIX)
app.include_router(alerts_router, prefix=API_PREFIX)


# ── Health Endpoints ──────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/ready", tags=["System"])
async def ready():
    """Readiness probe — checks DB connectivity."""
    try:
        from app.database import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        from fastapi import Response
        return Response(content=str(e), status_code=503)


# ── Sentry Integration ────────────────────────────────────
if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )
