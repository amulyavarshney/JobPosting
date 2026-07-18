"""Ashby public job board adapter."""

import re
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.scrapers.base import ScrapedJob
from app.scrapers.http_client import validate_url


def _org_slug(base_url: str) -> str:
    parsed = urlparse(base_url)
    path = parsed.path.strip("/")
    if path:
        return path.split("/")[0]
    if parsed.hostname and parsed.hostname.endswith("ashbyhq.com"):
        return parsed.hostname.split(".")[0]
    raise ValueError(f"Cannot parse Ashby org slug from {base_url}")


async def scrape_ashby(base_url: str) -> list[ScrapedJob]:
    settings = get_settings()
    slug = _org_slug(base_url)
    api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    validate_url(api_url)

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(api_url)
        response.raise_for_status()
        data = response.json()

    jobs: list[ScrapedJob] = []
    for item in data.get("jobs", []):
        description_html = item.get("descriptionHtml") or item.get("description") or ""
        text = re.sub(r"<[^>]+>", " ", description_html)
        text = re.sub(r"\s+", " ", text).strip()

        location = item.get("location") or ""
        if isinstance(location, dict):
            location = location.get("name") or ""

        jobs.append(
            ScrapedJob(
                external_id=item.get("id") or "",
                title=item.get("title") or "",
                company=data.get("organizationName") or slug,
                location=str(location),
                employment_type=item.get("employmentType") or "",
                description_html=description_html,
                description_text=text,
                apply_url=item.get("jobUrl") or item.get("applyUrl") or base_url,
                raw_url=item.get("jobUrl") or base_url,
            )
        )
    return jobs
