from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Draft, Job, ScrapeRun, Source, Template
from app.schemas import DashboardStats, DraftQueueItem, JobRead, ScrapeRunRead

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _job_to_read(job: Job) -> dict:
    data = JobRead.model_validate(job).model_dump()
    data["skills"] = job.skills
    return data


def _run_to_read(run: ScrapeRun, source_name: str | None) -> ScrapeRunRead:
    return ScrapeRunRead(
        id=run.id,
        source_id=run.source_id,
        source_name=source_name,
        status=run.status,
        jobs_found=run.jobs_found,
        jobs_created=run.jobs_created,
        jobs_updated=run.jobs_updated,
        jobs_archived=run.jobs_archived,
        error_message=run.error_message,
        duration_ms=run.duration_ms,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    since = datetime.now(UTC) - timedelta(hours=24)
    recent_jobs = db.query(Job).order_by(Job.scraped_at.desc()).limit(8).all()
    recent_runs = (
        db.query(ScrapeRun)
        .options(joinedload(ScrapeRun.source))
        .order_by(ScrapeRun.started_at.desc())
        .limit(8)
        .all()
    )
    pending = (
        db.query(Draft)
        .options(joinedload(Draft.job))
        .filter(Draft.status == "draft")
        .order_by(Draft.updated_at.desc())
        .limit(10)
        .all()
    )
    source_names = {s.id: s.name for s in db.query(Source).all()}

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
        drafts_reviewed=db.query(Draft)
        .filter(Draft.status.in_(["reviewed", "approved"]))
        .count(),
        drafts_pending=db.query(Draft).filter(Draft.status == "draft").count(),
        scrape_runs_24h=db.query(ScrapeRun).filter(ScrapeRun.started_at >= since).count(),
        scrape_failures_24h=db.query(ScrapeRun)
        .filter(ScrapeRun.started_at >= since, ScrapeRun.status == "failed")
        .count(),
        templates_total=db.query(Template).count(),
        recent_jobs=[_job_to_read(j) for j in recent_jobs],
        recent_runs=[
            _run_to_read(r, source_names.get(r.source_id) or (r.source.name if r.source else None))
            for r in recent_runs
        ],
        pending_drafts=[
            DraftQueueItem(
                id=d.id,
                job_id=d.job_id,
                channel=d.channel,
                status=d.status,
                job_title=d.job.title if d.job else "",
                company=d.job.company if d.job else "",
                updated_at=d.updated_at,
            )
            for d in pending
        ],
    )
