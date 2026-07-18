"""Local Jinja2 template rendering and prompt pack builder."""

from __future__ import annotations

import json
from types import SimpleNamespace

from jinja2 import BaseLoader, Environment, select_autoescape
from sqlalchemy.orm import Session

from app.models import BrandProfile, Draft, Job, Template

_ENV = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(default=False),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _job_context(job: Job) -> SimpleNamespace:
    return SimpleNamespace(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        employment_type=job.employment_type,
        salary_text=job.salary_text,
        description_html=job.description_html,
        description_text=job.description_text,
        skills=job.skills,
        apply_url=job.apply_url,
        external_id=job.external_id,
        posted_at=job.posted_at.isoformat() if job.posted_at else None,
        status=getattr(job, "status", "active"),
    )


def render_template(template: Template, job: Job, body_override: str | None = None) -> str:
    body = body_override if body_override is not None else template.body
    jinja_template = _ENV.from_string(body)
    return jinja_template.render(job=_job_context(job)).strip()


def get_brand_profile(db: Session) -> BrandProfile | None:
    return db.query(BrandProfile).order_by(BrandProfile.id.asc()).first()


def build_prompt_pack(
    draft: Draft,
    job: Job,
    template: Template,
    requirement: str = "",
    brand: BrandProfile | None = None,
) -> str:
    job_json = {
        "id": job.id,
        "title": job.title or "",
        "company": job.company or "",
        "location": job.location or "",
        "employment_type": job.employment_type or "",
        "salary_text": job.salary_text or "",
        "description_text": (job.description_text or "")[:3000],
        "skills": job.skills,
        "apply_url": job.apply_url or "",
    }

    sections = [
        "# JobPosting AI Polish Task",
        "",
        "You are polishing job marketing copy for a specific channel. "
        "Return ONLY the revised copy — no preamble, no markdown fences unless the channel needs it.",
        "",
        f"## Channel: {draft.channel}",
        "",
        "## Polish instructions",
        template.polish_instructions or "(Use your best judgment for this channel.)",
    ]

    if brand:
        sections.extend(
            [
                "",
                "## Brand voice",
                f"- Organization: {brand.organization_name or '(not set)'}",
                f"- Tone: {brand.tone or '(not set)'}",
            ]
        )
        if brand.voice_notes:
            sections.append(f"- Voice notes: {brand.voice_notes}")
        if brand.banned_words:
            sections.append(f"- Avoid these words/phrases: {brand.banned_words}")
        if brand.hashtag_policy:
            sections.append(f"- Hashtag policy: {brand.hashtag_policy}")
        if brand.cta_preference:
            sections.append(f"- CTA preference: {brand.cta_preference}")

    sections.extend(
        [
            "",
            "## Job context (JSON)",
            "```json",
            json.dumps(job_json, indent=2),
            "```",
            "",
            "## Current draft",
            draft.content,
        ]
    )

    if requirement.strip():
        sections.extend(["", "## Custom requirement", requirement.strip()])

    sections.extend(["", "## Output", "Provide the polished final copy only."])
    return "\n".join(sections)
