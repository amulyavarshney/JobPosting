"""JSON-LD and HTML job extractors."""

import json
import re
from html import unescape
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.base import ScrapedJob


def _strip_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    return re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True)).strip()


def _parse_json_ld_job(data: dict, page_url: str) -> ScrapedJob | None:
    job_type = data.get("@type", "")
    types = job_type if isinstance(job_type, list) else [job_type]
    if "JobPosting" not in types:
        return None

    title = data.get("title") or data.get("name") or ""
    description_html = data.get("description") or ""
    description_text = _strip_html(description_html) if "<" in description_html else description_html

    org = data.get("hiringOrganization") or {}
    if isinstance(org, str):
        company = org
    else:
        company = org.get("name") or ""

    location = ""
    job_location = data.get("jobLocation")
    if isinstance(job_location, dict):
        addr = job_location.get("address") or {}
        if isinstance(addr, dict):
            parts = [addr.get("addressLocality"), addr.get("addressRegion"), addr.get("addressCountry")]
            location = ", ".join(p for p in parts if p)
        elif isinstance(addr, str):
            location = addr
    elif isinstance(job_location, list) and job_location:
        first = job_location[0]
        if isinstance(first, dict):
            addr = first.get("address") or {}
            if isinstance(addr, dict):
                parts = [addr.get("addressLocality"), addr.get("addressRegion")]
                location = ", ".join(p for p in parts if p)

    employment_type = data.get("employmentType") or ""
    if isinstance(employment_type, list):
        employment_type = ", ".join(employment_type)

    salary_text = ""
    base_salary = data.get("baseSalary") or {}
    if isinstance(base_salary, dict):
        value = base_salary.get("value") or {}
        if isinstance(value, dict):
            min_val = value.get("minValue") or value.get("value")
            max_val = value.get("maxValue")
            currency = base_salary.get("currency") or value.get("unitText") or ""
            if min_val and max_val:
                salary_text = f"{min_val}-{max_val} {currency}".strip()
            elif min_val:
                salary_text = f"{min_val} {currency}".strip()

    apply_url = data.get("url") or data.get("directApply") or page_url
    if isinstance(apply_url, bool):
        apply_url = page_url

    identifier = data.get("identifier") or {}
    external_id = ""
    if isinstance(identifier, dict):
        external_id = str(identifier.get("value") or identifier.get("@id") or "")
    elif identifier:
        external_id = str(identifier)

    if not external_id:
        external_id = re.sub(r"[^a-zA-Z0-9]+", "-", f"{company}-{title}".lower()).strip("-")

    posted_at = None
    date_posted = data.get("datePosted")
    if date_posted:
        try:
            from datetime import datetime

            posted_at = datetime.fromisoformat(date_posted.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            posted_at = None

    skills: list[str] = []
    for skill in data.get("skills") or []:
        if isinstance(skill, str):
            skills.append(skill)
        elif isinstance(skill, dict):
            name = skill.get("name")
            if name:
                skills.append(name)

    return ScrapedJob(
        external_id=external_id,
        title=title,
        company=company,
        location=location,
        employment_type=str(employment_type),
        salary_text=salary_text,
        description_html=description_html if "<" in description_html else f"<p>{description_html}</p>",
        description_text=description_text,
        skills=skills,
        apply_url=str(apply_url),
        posted_at=posted_at,
        raw_url=page_url,
        needs_manual_fill=not title or not description_text,
    )


def extract_from_html(html: str, page_url: str) -> ScrapedJob:
    soup = BeautifulSoup(html, "lxml")

    # JSON-LD first
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue
            if "@graph" in item:
                for node in item["@graph"]:
                    if isinstance(node, dict):
                        job = _parse_json_ld_job(node, page_url)
                        if job and job.title:
                            return job
            job = _parse_json_ld_job(item, page_url)
            if job and job.title:
                return job

    # OpenGraph / meta fallbacks
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"]
    if not title and soup.title:
        title = soup.title.get_text(strip=True)

    description = ""
    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    if og_desc and og_desc.get("content"):
        description = og_desc["content"]

    company = ""
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content"):
        company = og_site["content"]

    apply_url = page_url
    og_url = soup.find("meta", property="og:url")
    if og_url and og_url.get("content"):
        apply_url = urljoin(page_url, og_url["content"])

    # Heuristic: largest article/main content block
    description_html = ""
    for selector in ["article", "main", '[class*="job-description"]', '[class*="description"]', ".content"]:
        el = soup.select_one(selector)
        if el:
            description_html = str(el)
            break

    if not description_html and description:
        description_html = f"<p>{unescape(description)}</p>"

    description_text = _strip_html(description_html) or description

    external_id = re.sub(r"[^a-zA-Z0-9]+", "-", page_url.lower()).strip("-")[:200]

    return ScrapedJob(
        external_id=external_id,
        title=title,
        company=company,
        location="",
        description_html=description_html,
        description_text=description_text,
        apply_url=apply_url,
        raw_url=page_url,
        needs_manual_fill=not title or len(description_text) < 50,
    )
