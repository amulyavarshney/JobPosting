"""Simple in-memory sliding-window rate limiter."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

from app.config import get_settings

_lock = Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(request: Request, *, scrape: bool = False) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return

    limit = settings.scrape_rate_limit_requests if scrape else settings.rate_limit_requests
    window = (
        settings.scrape_rate_limit_window_seconds
        if scrape
        else settings.rate_limit_window_seconds
    )
    key = f"{'scrape' if scrape else 'api'}:{_client_ip(request)}"
    now = time.monotonic()

    with _lock:
        bucket = _buckets[key]
        while bucket and bucket[0] <= now - window:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({limit}/{window}s). Retry shortly.",
            )
        bucket.append(now)
