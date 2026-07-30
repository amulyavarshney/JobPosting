from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScrapeRun, Source
from app.rate_limit import check_rate_limit
from app.schemas import (
    ScrapeAllResponse,
    ScrapeResponse,
    ScrapeRunRead,
    SourceCreate,
    SourceRead,
    SourceUpdate,
)
from app.scrapers.service import run_scrape_for_source

router = APIRouter(prefix="/sources", tags=["sources"])

VALID_KINDS = {"greenhouse", "lever", "ashby", "workday", "custom"}


@router.get("", response_model=list[SourceRead])
def list_sources(db: Session = Depends(get_db)):
    return db.query(Source).order_by(Source.created_at.desc()).all()


@router.post("", response_model=SourceRead, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    if payload.kind not in VALID_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {sorted(VALID_KINDS)}")

    source = Source(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def _run_to_response(run: ScrapeRun) -> ScrapeResponse:
    return ScrapeResponse(
        source_id=run.source_id,
        run_id=run.id,
        jobs_found=run.jobs_found,
        jobs_created=run.jobs_created,
        jobs_updated=run.jobs_updated,
        jobs_archived=run.jobs_archived,
        status=run.status,
        error_message=run.error_message,
        duration_ms=run.duration_ms,
    )


@router.post("/scrape-all", response_model=ScrapeAllResponse)
async def scrape_all(request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, scrape=True)
    sources = db.query(Source).filter(Source.enabled.is_(True)).all()
    results: list[ScrapeResponse] = []
    for source in sources:
        run = await run_scrape_for_source(db, source)
        results.append(_run_to_response(run))
    return ScrapeAllResponse(results=results, sources_scraped=len(results))


@router.get("/{source_id}", response_model=SourceRead)
def get_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=SourceRead)
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    data = payload.model_dump(exclude_unset=True)
    if "kind" in data and data["kind"] not in VALID_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {sorted(VALID_KINDS)}")

    for key, value in data.items():
        setattr(source, key, value)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()


@router.post("/{source_id}/scrape", response_model=ScrapeResponse)
async def scrape_source(
    source_id: int, request: Request, db: Session = Depends(get_db)
):
    check_rate_limit(request, scrape=True)
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if not source.enabled:
        raise HTTPException(status_code=400, detail="Source is disabled")

    run = await run_scrape_for_source(db, source)
    if run.status == "failed":
        raise HTTPException(
            status_code=502,
            detail=run.error_message or "Scrape failed",
        )
    return _run_to_response(run)


@router.get("/{source_id}/runs", response_model=list[ScrapeRunRead])
def list_source_runs(source_id: int, limit: int = 20, db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    runs = (
        db.query(ScrapeRun)
        .filter(ScrapeRun.source_id == source_id)
        .order_by(ScrapeRun.started_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [
        ScrapeRunRead(
            id=r.id,
            source_id=r.source_id,
            source_name=source.name,
            status=r.status,
            jobs_found=r.jobs_found,
            jobs_created=r.jobs_created,
            jobs_updated=r.jobs_updated,
            jobs_archived=r.jobs_archived,
            error_message=r.error_message,
            duration_ms=r.duration_ms,
            started_at=r.started_at,
            finished_at=r.finished_at,
        )
        for r in runs
    ]
