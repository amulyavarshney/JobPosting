from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Draft, Job, ScrapeRun, Source, Template
from app.schemas import DashboardStats, JobRead

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _job_to_read(job: Job) -> dict:
    data = JobRead.model_validate(job).model_dump()
    data["skills"] = job.skills
    return data


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    since = datetime.now(UTC) - timedelta(hours=24)
    recent_jobs = db.query(Job).order_by(Job.scraped_at.desc()).limit(8).all()
    recent_runs = db.query(ScrapeRun).order_by(ScrapeRun.started_at.desc()).limit(8).all()

    return DashboardStats(
        sources_total=db.query(Source).count(),
        sources_enabled=db.query(Source).filter(Source.enabled.is_(True)).count(),
        jobs_active=db.query(Job).filter(Job.status == "active").count(),
        jobs_archived=db.query(Job).filter(Job.status == "archived").count(),
        jobs_needs_manual_fill=db.query(Job)
        .filter(Job.needs_manual_fill.is_(True), Job.status == "active")
        .count(),
        jobs_changed=db.query(Job)
        .filter(Job.content_changed.is_(True), Job.status == "active")
        .count(),
        drafts_total=db.query(Draft).count(),
        drafts_reviewed=db.query(Draft).filter(Draft.status.in_(["reviewed", "approved"])).count(),
        scrape_runs_24h=db.query(ScrapeRun).filter(ScrapeRun.started_at >= since).count(),
        scrape_failures_24h=db.query(ScrapeRun)
        .filter(ScrapeRun.started_at >= since, ScrapeRun.status == "failed")
        .count(),
        templates_total=db.query(Template).count(),
        recent_jobs=[_job_to_read(j) for j in recent_jobs],
        recent_runs=recent_runs,
    )
