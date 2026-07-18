"""Scraper orchestration with run logging and job lifecycle."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Job, ScrapeRun, Source, utcnow
from app.scrapers.ashby import scrape_ashby
from app.scrapers.base import ScrapedJob
from app.scrapers.greenhouse import scrape_greenhouse
from app.scrapers.lever import scrape_lever
from app.scrapers.workday import scrape_custom_url, scrape_workday

logger = logging.getLogger(__name__)


async def fetch_jobs_from_source(source: Source) -> list[ScrapedJob]:
    kind = source.kind.lower()
    if kind == "greenhouse":
        return await scrape_greenhouse(source.base_url)
    if kind == "lever":
        return await scrape_lever(source.base_url)
    if kind == "ashby":
        return await scrape_ashby(source.base_url)
    if kind == "workday":
        return await scrape_workday(source.base_url)
    if kind == "custom":
        return await scrape_custom_url(source.base_url)
    raise ValueError(f"Unknown source kind: {source.kind}")


def upsert_scraped_jobs(
    db: Session,
    source: Source,
    scraped: list[ScrapedJob],
    *,
    archive_missing: bool | None = None,
) -> tuple[int, int, int]:
    """Upsert scraped jobs. Returns (created, updated, archived)."""
    settings = get_settings()
    if archive_missing is None:
        archive_missing = settings.archive_missing_jobs

    created = 0
    updated = 0
    now = utcnow()
    seen_external_ids: set[str] = set()
    seen_job_ids: set[int] = set()

    for item in scraped:
        external_id = (item.external_id or "").strip() or None
        apply_url = (item.apply_url or "").strip()
        existing = None
        if external_id:
            seen_external_ids.add(external_id)
            existing = (
                db.query(Job)
                .filter(Job.source_id == source.id, Job.external_id == external_id)
                .first()
            )
        elif apply_url:
            existing = (
                db.query(Job)
                .filter(Job.source_id == source.id, Job.apply_url == apply_url)
                .first()
            )

        if existing:
            prev_hash = existing.content_hash
            existing.title = item.title or existing.title
            existing.company = item.company or existing.company
            existing.location = item.location or existing.location
            existing.employment_type = item.employment_type or existing.employment_type
            existing.salary_text = item.salary_text or existing.salary_text
            existing.description_html = item.description_html or existing.description_html
            existing.description_text = item.description_text or existing.description_text
            if item.skills:
                existing.skills = item.skills
            existing.apply_url = item.apply_url or existing.apply_url
            existing.posted_at = item.posted_at or existing.posted_at
            existing.raw_url = item.raw_url or existing.raw_url
            existing.needs_manual_fill = item.needs_manual_fill
            existing.scraped_at = now
            existing.last_seen_at = now
            existing.status = "active"
            new_hash = existing.compute_hash()
            existing.content_changed = bool(prev_hash and prev_hash != new_hash)
            existing.content_hash = new_hash
            seen_job_ids.add(existing.id)
            updated += 1
        else:
            job = Job(
                source_id=source.id,
                external_id=external_id,
                title=item.title,
                company=item.company,
                location=item.location,
                employment_type=item.employment_type,
                salary_text=item.salary_text,
                description_html=item.description_html,
                description_text=item.description_text,
                apply_url=apply_url,
                posted_at=item.posted_at,
                raw_url=item.raw_url,
                needs_manual_fill=item.needs_manual_fill,
                scraped_at=now,
                last_seen_at=now,
                status="active",
                content_changed=False,
            )
            job.skills = item.skills
            job.content_hash = job.compute_hash()
            db.add(job)
            db.flush()
            seen_job_ids.add(job.id)
            created += 1

    archived = 0
    if archive_missing and scraped:
        active_jobs = (
            db.query(Job)
            .filter(Job.source_id == source.id, Job.status == "active")
            .all()
        )
        for job in active_jobs:
            if job.id in seen_job_ids:
                continue
            if job.external_id and job.external_id in seen_external_ids:
                continue
            job.status = "archived"
            archived += 1

    db.commit()
    return created, updated, archived


async def run_scrape_for_source(db: Session, source: Source) -> ScrapeRun:
    run = ScrapeRun(source_id=source.id, status="running", started_at=utcnow())
    db.add(run)
    db.commit()
    db.refresh(run)

    started = time.perf_counter()
    try:
        scraped = await fetch_jobs_from_source(source)
        created, updated, archived = upsert_scraped_jobs(db, source, scraped)
        db.refresh(run)
        db.refresh(source)
        run.status = "success"
        run.jobs_found = len(scraped)
        run.jobs_created = created
        run.jobs_updated = updated
        run.jobs_archived = archived
        run.error_message = None
        source.last_error = None
        source.last_run_status = "success"
        source.last_scraped_at = utcnow()
        logger.info(
            "Scrape ok source=%s found=%s created=%s updated=%s archived=%s",
            source.id,
            len(scraped),
            created,
            updated,
            archived,
        )
    except Exception as exc:
        logger.exception("Scrape failed source=%s", source.id)
        db.rollback()
        run = db.query(ScrapeRun).filter(ScrapeRun.id == run.id).first() or run
        source = db.query(Source).filter(Source.id == source.id).first() or source
        run.status = "failed"
        run.error_message = str(exc)[:2000]
        source.last_error = str(exc)[:2000]
        source.last_run_status = "failed"

    run.duration_ms = (time.perf_counter() - started) * 1000
    run.finished_at = utcnow()
    db.commit()
    db.refresh(run)
    return run


def sources_due_for_scrape(db: Session) -> list[Source]:
    now = datetime.now(UTC)
    sources = db.query(Source).filter(Source.enabled.is_(True)).all()
    due: list[Source] = []
    for source in sources:
        if not source.scrape_interval_minutes or source.scrape_interval_minutes <= 0:
            continue
        if source.last_scraped_at is None:
            due.append(source)
            continue
        last = source.last_scraped_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        elapsed_min = (now - last).total_seconds() / 60.0
        if elapsed_min >= source.scrape_interval_minutes:
            due.append(source)
    return due
