import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job
from app.schemas import JobCreate, JobRead, JobUpdate, PaginatedJobs

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_to_read(job: Job) -> dict:
    data = JobRead.model_validate(job).model_dump()
    data["skills"] = job.skills
    return data


@router.get("", response_model=PaginatedJobs)
def list_jobs(
    q: str | None = None,
    needs_manual_fill: bool | None = None,
    source_id: int | None = None,
    status: str | None = Query(default="active"),
    content_changed: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Job)
    if status and status != "all":
        query = query.filter(Job.status == status)
    if needs_manual_fill is not None:
        query = query.filter(Job.needs_manual_fill == needs_manual_fill)
    if source_id is not None:
        query = query.filter(Job.source_id == source_id)
    if content_changed is not None:
        query = query.filter(Job.content_changed == content_changed)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(like),
                Job.company.ilike(like),
                Job.location.ilike(like),
            )
        )

    total = query.count()
    pages = max(1, math.ceil(total / page_size))
    jobs = (
        query.order_by(Job.scraped_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedJobs(
        items=[_job_to_read(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=JobRead, status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    skills = data.pop("skills", [])
    job = Job(**data)
    job.skills = skills
    job.content_hash = job.compute_hash()
    db.add(job)
    db.commit()
    db.refresh(job)
    return _job_to_read(job)


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_read(job)


@router.patch("/{job_id}", response_model=JobRead)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    data = payload.model_dump(exclude_unset=True)
    skills = data.pop("skills", None)
    if "status" in data and data["status"] not in {"active", "archived", "closed"}:
        raise HTTPException(status_code=400, detail="status must be active|archived|closed")
    for key, value in data.items():
        setattr(job, key, value)
    if skills is not None:
        job.skills = skills
    job.content_hash = job.compute_hash()
    db.commit()
    db.refresh(job)
    return _job_to_read(job)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
