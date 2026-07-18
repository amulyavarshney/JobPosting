"""Lever public postings adapter."""

import re
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.scrapers.base import ScrapedJob
from app.scrapers.http_client import validate_url


def _company_slug(base_url: str) -> str:
    parsed = urlparse(base_url)
    path = parsed.path.strip("/")
    if path:
        return path.split("/")[0]
    if parsed.hostname and parsed.hostname.endswith("lever.co"):
        return parsed.hostname.split(".")[0]
    raise ValueError(f"Cannot parse Lever company slug from {base_url}")


async def scrape_lever(base_url: str) -> list[ScrapedJob]:
    settings = get_settings()
    slug = _company_slug(base_url)
    api_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    validate_url(api_url)

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        response = await client.get(api_url)
        response.raise_for_status()
        data = response.json()

    jobs: list[ScrapedJob] = []
    for item in data:
        categories = item.get("categories") or {}
        location = categories.get("location") or ""
        commitment = categories.get("commitment") or ""
        description_html = (item.get("description") or "") + (item.get("descriptionPlain") or "")
        if item.get("lists"):
            for lst in item["lists"]:
                description_html += lst.get("text", "") or ""

        text = item.get("descriptionPlain") or re.sub(r"<[^>]+>", " ", description_html)
        text = re.sub(r"\s+", " ", text).strip()

        jobs.append(
            ScrapedJob(
                external_id=item.get("id") or item.get("shortCode") or "",
                title=item.get("text") or "",
                company=slug,
                location=location,
                employment_type=commitment,
                description_html=description_html,
                description_text=text,
                apply_url=item.get("hostedUrl") or item.get("applyUrl") or base_url,
                raw_url=item.get("hostedUrl") or base_url,
            )
        )
    return jobs
