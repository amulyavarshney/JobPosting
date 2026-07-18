"""Workday public careers adapter (best-effort JSON/HTML)."""

import json
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.extractors.custom import extract_from_html
from app.scrapers.base import ScrapedJob
from app.scrapers.http_client import fetch_url, validate_url


def _workday_site_path(base_url: str) -> tuple[str, str]:
    parsed = urlparse(base_url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2:
        return parts[0], parts[1]
    raise ValueError(f"Cannot parse Workday site path from {base_url}. Expected .../site/lang")


async def scrape_workday(base_url: str) -> list[ScrapedJob]:
    settings = get_settings()
    validate_url(base_url)
    site, lang = _workday_site_path(base_url)
    origin = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"

    cx_url = urljoin(origin, f"/wday/cxs/{site}/{lang}/jobs")
    validate_url(cx_url)

    jobs: list[ScrapedJob] = []
    offset = 0
    limit = 20

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        while True:
            payload = {"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""}
            response = await client.post(cx_url, json=payload)
            if response.status_code >= 400:
                # Fallback: scrape listing page HTML
                _, html = await fetch_url(base_url)
                soup = BeautifulSoup(html, "lxml")
                for link in soup.select('a[data-automation-id="jobTitle"]'):
                    href = link.get("href") or ""
                    title = link.get_text(strip=True)
                    job_url = urljoin(base_url, href)
                    jobs.append(
                        ScrapedJob(
                            external_id=re.sub(r"[^a-zA-Z0-9]+", "-", job_url.lower())[:200],
                            title=title,
                            company=site,
                            apply_url=job_url,
                            raw_url=job_url,
                            needs_manual_fill=True,
                        )
                    )
                return jobs

            data = response.json()
            postings = data.get("jobPostings") or []
            if not postings:
                break

            for item in postings:
                external_path = item.get("externalPath") or ""
                title = item.get("title") or ""
                location = item.get("locationsText") or ""
                bullet_fields = item.get("bulletFields") or []
                job_url = urljoin(origin, external_path) if external_path else base_url

                description_html = ""
                description_text = ""
                if external_path:
                    detail_url = urljoin(origin, f"/wday/cxs/{site}/{lang}{external_path}")
                    try:
                        detail_resp = await client.get(detail_url)
                        if detail_resp.status_code < 400:
                            detail = detail_resp.json()
                            info = detail.get("jobPostingInfo") or detail
                            description_html = info.get("jobDescription") or ""
                            description_text = re.sub(r"<[^>]+>", " ", description_html)
                            description_text = re.sub(r"\s+", " ", description_text).strip()
                            location = info.get("location") or location
                    except (json.JSONDecodeError, httpx.HTTPError):
                        pass

                jobs.append(
                    ScrapedJob(
                        external_id=item.get("jobPostingId") or external_path or title,
                        title=title,
                        company=site,
                        location=location,
                        description_html=description_html,
                        description_text=description_text,
                        skills=[str(b) for b in bullet_fields if b],
                        apply_url=job_url,
                        raw_url=job_url,
                        needs_manual_fill=not description_text,
                    )
                )

            total = data.get("total") or len(jobs)
            offset += limit
            if offset >= total:
                break

    return jobs


async def scrape_custom_url(url: str) -> list[ScrapedJob]:
    final_url, html = await fetch_url(url)
    job = extract_from_html(html, final_url)
    return [job]
