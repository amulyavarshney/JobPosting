"""Background scheduler for automatic source scrapes."""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import SessionLocal
from app.scrapers.service import run_scrape_for_source, sources_due_for_scrape

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_scrape_lock = asyncio.Lock()


async def _tick() -> None:
    if _scrape_lock.locked():
        logger.debug("Scheduler tick skipped — scrape already running")
        return

    async with _scrape_lock:
        db = SessionLocal()
        try:
            due = sources_due_for_scrape(db)
            if not due:
                return
            logger.info("Scheduler scraping %s source(s)", len(due))
            for source in due:
                try:
                    await run_scrape_for_source(db, source)
                except Exception:
                    logger.exception("Scheduled scrape failed for source=%s", source.id)
        finally:
            db.close()


def start_scheduler() -> None:
    global _scheduler
    settings = get_settings()
    if not settings.enable_scheduler:
        logger.info("Scheduler disabled")
        return
    if _scheduler is not None:
        return

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _tick,
        "interval",
        seconds=settings.scheduler_tick_seconds,
        id="scrape_tick",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started (tick=%ss)", settings.scheduler_tick_seconds
    )


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
