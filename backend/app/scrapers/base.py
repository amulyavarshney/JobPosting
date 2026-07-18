"""Normalized job data from scrapers."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScrapedJob:
    external_id: str
    title: str = ""
    company: str = ""
    location: str = ""
    employment_type: str = ""
    salary_text: str = ""
    description_html: str = ""
    description_text: str = ""
    skills: list[str] = field(default_factory=list)
    apply_url: str = ""
    posted_at: datetime | None = None
    raw_url: str = ""
    needs_manual_fill: bool = False
