"""Greenhouse public board adapter."""

import re
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.scrapers.base import ScrapedJob
from app.scrapers.http_client import validate_url


def _board_token(base_url: str) -> str:
    parsed = urlparse(base_url)
    path = parsed.path.strip("/")
    if path:
        return path.split("/")[0]
    host_parts = parsed.hostname.split(".") if parsed.hostname else []
    if "boards" in host_parts:
        idx = host_parts.index("boards")
        if idx + 1 < len(host_parts):
            return host_parts[idx + 1]
    raise ValueError(f"Cannot parse Greenhouse board token from {base_url}")


async def scrape_greenhouse(base_url: str) -> list[ScrapedJob]:
    settings = get_settings()
    token = _board_token(base_url)
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    validate_url(api_url)

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(api_url)
        response.raise_for_status()
        data = response.json()

    jobs: list[ScrapedJob] = []
    for item in data.get("jobs", []):
        loc = item.get("location") or {}
        location = loc.get("name") if isinstance(loc, dict) else str(loc)
        content = item.get("content") or ""
        text = re.sub(r"<[^>]+>", " ", content)
        text = re.sub(r"\s+", " ", text).strip()

        jobs.append(
            ScrapedJob(
                external_id=str(item.get("id", "")),
                title=item.get("title") or "",
                company=data.get("name") or token,
                location=location or "",
                description_html=content,
                description_text=text,
                apply_url=item.get("absolute_url") or base_url,
                raw_url=item.get("absolute_url") or base_url,
                needs_manual_fill=not item.get("title"),
            )
        )
    return jobs
