from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.generation.renderer import build_prompt_pack, get_brand_profile, render_template
from app.models import Draft, Job, Revision, Template
from app.schemas import (
    BulkGenerateRequest,
    BulkGenerateResponse,
    DraftRead,
    DraftUpdate,
    ExportResponse,
    GenerateDraftsRequest,
    ImportResultRequest,
    PromptPackRequest,
    PromptPackResponse,
    RevisionRead,
)

router = APIRouter(prefix="/drafts", tags=["drafts"])


PROTECTED_STATUSES = {"reviewed", "approved", "exported"}


def _generate_for_job(
    db: Session,
    job: Job,
    templates: list[Template],
    *,
    overwrite_reviewed: bool = False,
) -> list[Draft]:
    results: list[Draft] = []
    for template in templates:
        content = render_template(template, job)
        existing = (
            db.query(Draft)
            .filter(Draft.job_id == job.id, Draft.template_id == template.id)
            .first()
        )
        if existing:
            if existing.status in PROTECTED_STATUSES and not overwrite_reviewed:
                results.append(existing)
                continue
            if existing.content != content:
                db.add(
                    Revision(
                        draft_id=existing.id,
                        requirement="Regenerated from template",
                        before=existing.content,
                        after=content,
                        source="generate",
                    )
                )
            existing.content = content
            existing.channel = template.channel
            existing.status = "draft"
            results.append(existing)
        else:
            draft = Draft(
                job_id=job.id,
                template_id=template.id,
                channel=template.channel,
                content=content,
                status="draft",
            )
            db.add(draft)
            results.append(draft)
    return results


@router.get("", response_model=list[DraftRead])
def list_drafts(
    job_id: int | None = None,
    status: str | None = None,
    channel: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Draft)
    if job_id is not None:
        query = query.filter(Draft.job_id == job_id)
    if status:
        query = query.filter(Draft.status == status)
    if channel:
        query = query.filter(Draft.channel == channel)
    return query.order_by(Draft.updated_at.desc()).all()


@router.post("/generate", response_model=list[DraftRead])
def generate_drafts(payload: GenerateDraftsRequest, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    templates = db.query(Template).filter(Template.id.in_(payload.template_ids)).all()
    if not templates:
        raise HTTPException(status_code=400, detail="No valid templates selected")

    results = _generate_for_job(
        db, job, templates, overwrite_reviewed=payload.overwrite_reviewed
    )
    db.commit()
    for draft in results:
        db.refresh(draft)
    return results


@router.post("/generate-bulk", response_model=BulkGenerateResponse)
def generate_bulk(payload: BulkGenerateRequest, db: Session = Depends(get_db)):
    templates = db.query(Template).filter(Template.id.in_(payload.template_ids)).all()
    if not templates:
        raise HTTPException(status_code=400, detail="No valid templates selected")

    jobs = db.query(Job).filter(Job.id.in_(payload.job_ids)).all()
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found")

    all_drafts: list[Draft] = []
    for job in jobs:
        all_drafts.extend(
            _generate_for_job(
                db, job, templates, overwrite_reviewed=payload.overwrite_reviewed
            )
        )

    db.commit()
    for draft in all_drafts:
        db.refresh(draft)
    return BulkGenerateResponse(drafts=all_drafts, jobs_processed=len(jobs))


@router.get("/{draft_id}", response_model=DraftRead)
def get_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.patch("/{draft_id}", response_model=DraftRead)
def update_draft(draft_id: int, payload: DraftUpdate, db: Session = Depends(get_db)):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    before = draft.content
    if payload.content is not None and payload.content != before:
        db.add(
            Revision(
                draft_id=draft.id,
                requirement="Manual edit",
                before=before,
                after=payload.content,
                source="manual",
            )
        )
        draft.content = payload.content
    if payload.status is not None:
        if payload.status not in {"draft", "reviewed", "approved", "exported"}:
            raise HTTPException(
                status_code=400,
                detail="status must be draft|reviewed|approved|exported",
            )
        draft.status = payload.status

    db.commit()
    db.refresh(draft)
    return draft


@router.post("/{draft_id}/prompt-pack", response_model=PromptPackResponse)
def create_prompt_pack(
    draft_id: int, payload: PromptPackRequest, db: Session = Depends(get_db)
):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    job = db.query(Job).filter(Job.id == draft.job_id).first()
    template = db.query(Template).filter(Template.id == draft.template_id).first()
    if not job or not template:
        raise HTTPException(status_code=404, detail="Job or template not found")

    brand = get_brand_profile(db)
    prompt = build_prompt_pack(draft, job, template, payload.requirement, brand=brand)
    return PromptPackResponse(prompt=prompt, draft_id=draft.id, channel=draft.channel)


@router.post("/{draft_id}/import", response_model=DraftRead)
def import_ai_result(
    draft_id: int, payload: ImportResultRequest, db: Session = Depends(get_db)
):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    before = draft.content
    db.add(
        Revision(
            draft_id=draft.id,
            requirement=payload.requirement or "AI import",
            before=before,
            after=payload.content,
            source="import",
        )
    )
    draft.content = payload.content
    draft.status = "reviewed"
    db.commit()
    db.refresh(draft)
    return draft


@router.get("/{draft_id}/export", response_model=ExportResponse)
def export_draft(
    draft_id: int,
    format: str = Query(default="text", pattern="^(text|markdown|json)$"),
    db: Session = Depends(get_db),
):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    job = db.query(Job).filter(Job.id == draft.job_id).first()
    title = job.title if job else ""
    company = job.company if job else ""
    markdown = f"# {title} — {company}\n\n**Channel:** {draft.channel}\n\n{draft.content}\n"
    return ExportResponse(
        draft_id=draft.id,
        channel=draft.channel,
        content=draft.content,
        job_title=title,
        company=company,
        format=format,
        markdown=markdown if format in {"markdown", "json"} else None,
    )


@router.get("/{draft_id}/export/download")
def download_export(
    draft_id: int,
    format: str = Query(default="text", pattern="^(text|markdown)$"),
    db: Session = Depends(get_db),
):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    job = db.query(Job).filter(Job.id == draft.job_id).first()
    title = (job.title if job else "draft").replace("/", "-")[:60]
    if format == "markdown":
        body = f"# {job.title if job else ''} — {job.company if job else ''}\n\n{draft.content}\n"
        media = "text/markdown"
        filename = f"{title}-{draft.channel}.md"
    else:
        body = draft.content
        media = "text/plain"
        filename = f"{title}-{draft.channel}.txt"
    return PlainTextResponse(
        content=body,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{draft_id}/revisions", response_model=list[RevisionRead])
def list_revisions(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return (
        db.query(Revision)
        .filter(Revision.draft_id == draft_id)
        .order_by(Revision.created_at.desc())
        .all()
    )
