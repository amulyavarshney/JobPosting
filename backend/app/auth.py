"""Optional API key authentication for write operations."""

from fastapi import Header, HTTPException, Request

from app.config import get_settings

PUBLIC_PATHS = {
    "/api/health",
    "/api/health/live",
    "/api/health/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
}

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def api_key_dependency(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    settings = get_settings()
    if not settings.api_key_required:
        return

    path = request.url.path
    if path in PUBLIC_PATHS or path.startswith("/assets"):
        return
    if request.method in SAFE_METHODS and path.startswith("/api/"):
        # Allow unauthenticated reads; protect mutations
        return
    if request.method in SAFE_METHODS and not path.startswith("/api/"):
        return

    expected = settings.api_key
    if not expected:
        raise HTTPException(status_code=503, detail="API key not configured for this environment")
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
