from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import analytics, brand, drafts, jobs, sources, templates
from app.api import settings as settings_api
from app.auth import api_key_dependency
from app.config import get_settings
from app.database import SessionLocal, engine, init_db
from app.logging_config import setup_logging
from app.rate_limit import check_rate_limit
from app.scheduler import start_scheduler, stop_scheduler
from app.seed import seed_brand_profile, seed_templates

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_json)
    logger.info("Starting %s v%s (%s)", settings.app_name, settings.app_version, settings.environment)
    init_db()
    db = SessionLocal()
    try:
        seed_templates(db)
        seed_brand_profile(db)
    finally:
        db.close()
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings_obj = get_settings()
    app = FastAPI(
        title=settings_obj.app_name,
        version=settings_obj.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings_obj.docs_enabled else None,
        redoc_url="/redoc" if settings_obj.docs_enabled else None,
        openapi_url="/openapi.json" if settings_obj.docs_enabled else None,
        dependencies=[Depends(api_key_dependency)],
    )

    if settings_obj.allowed_hosts_list != ["*"]:
        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=settings_obj.allowed_hosts_list
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings_obj.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        start = time.perf_counter()
        try:
            if request.url.path.startswith("/api/"):
                check_rate_limit(request)
            response = await call_next(request)
        except (HTTPException, StarletteHTTPException):
            raise
        except Exception:
            logger.exception("Unhandled error request_id=%s path=%s", request_id, request.url.path)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id},
            )
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.1f}"
        if settings_obj.is_production:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.path.startswith("/api/"):
            logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
                request_id,
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
        return response

    app.include_router(sources.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    app.include_router(templates.router, prefix="/api")
    app.include_router(drafts.router, prefix="/api")
    app.include_router(settings_api.router, prefix="/api")
    app.include_router(brand.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")

    @app.get("/api/health")
    @app.get("/api/health/live")
    def health_live():
        return {
            "status": "ok",
            "version": settings_obj.app_version,
            "environment": settings_obj.environment,
        }

    @app.get("/api/health/ready")
    def health_ready():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ready", "database": "ok"}
        except Exception as exc:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "database": str(exc)},
            )

    _mount_frontend(app, settings_obj)
    return app


def _mount_frontend(app: FastAPI, settings_obj) -> None:
    if not settings_obj.serve_frontend:
        return
    dist = Path(settings_obj.frontend_dist)
    if not dist.is_absolute():
        dist = (Path(__file__).resolve().parent.parent / dist).resolve()
    if not dist.exists():
        logger.info("Frontend dist not found at %s — API-only mode", dist)
        return

    assets = dist / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    index = dist / "index.html"

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        candidate = dist / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)

    logger.info("Serving frontend from %s", dist)


app = create_app()
