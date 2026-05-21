"""
Application factory.

Using the factory pattern (create_app()) instead of a module-level `app`
makes testing trivial — each test gets a fresh app instance.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.api.v1.router import router as api_v1_router
from app.api.v1.job_descriptions import router as job_description_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown logic. Runs once per process."""
    settings = get_settings()
    logger = get_logger(__name__)

    configure_logging(
        environment=settings.ENVIRONMENT,
        log_level="DEBUG" if settings.DEBUG else "INFO",
    )
    logger.info(f"app_startup | environment={settings.ENVIRONMENT} | version=1.0.0")

    yield  # Application runs here

    logger.info("app_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters — outermost runs first) ─────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.ALLOWED_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_v1_router)
    app.include_router(
        job_description_router,
        prefix="/job-descriptions",
        tags=["Job Descriptions"]
)
    # ── Health check ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["ops"], include_in_schema=False)
    async def health_check():
        return {"status": "ok", "environment": settings.ENVIRONMENT}

    return app


# Module-level app for uvicorn/gunicorn entrypoint
app = create_app()
