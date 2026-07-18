from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.generation.renderer import render_template
from app.models import Job, Template
from app.schemas import (
    TemplateCreate,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    TemplateRead,
    TemplateUpdate,
)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateRead])
def list_templates(channel: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Template)
    if channel:
        query = query.filter(Template.channel == channel)
    return query.order_by(Template.channel, Template.name).all()


@router.post("", response_model=TemplateRead, status_code=201)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    template = Template(**payload.model_dump())
    if template.is_default:
        db.query(Template).filter(Template.channel == template.channel).update(
            {"is_default": False}
        )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateRead)
def get_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.patch("/{template_id}", response_model=TemplateRead)
def update_template(template_id: int, payload: TemplateUpdate, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default"):
        channel = data.get("channel") or template.channel
        db.query(Template).filter(Template.channel == channel, Template.id != template_id).update(
            {"is_default": False}
        )

    for key, value in data.items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()


@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
def preview_template(
    template_id: int, payload: TemplatePreviewRequest, db: Session = Depends(get_db)
):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        content = render_template(template, job, body_override=payload.body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Template render error: {exc}") from exc
    return TemplatePreviewResponse(content=content)
