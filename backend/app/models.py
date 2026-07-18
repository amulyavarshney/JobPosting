import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    base_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    scrape_interval_minutes: Mapped[int] = mapped_column(Integer, default=0)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_run_status: Mapped[str] = mapped_column(String(32), default="never")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    jobs: Mapped[list["Job"]] = relationship(back_populates="source", cascade="all, delete-orphan")
    scrape_runs: Mapped[list["ScrapeRun"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_job_source_external"),
        Index("ix_jobs_scraped_at", "scraped_at"),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_company", "company"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    company: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    employment_type: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    salary_text: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    description_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    skills_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    apply_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    needs_manual_fill: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    content_changed: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped[Source | None] = relationship(back_populates="jobs")
    drafts: Mapped[list["Draft"]] = relationship(back_populates="job", cascade="all, delete-orphan")

    @property
    def skills(self) -> list[str]:
        if not self.skills_json:
            return []
        try:
            return json.loads(self.skills_json)
        except json.JSONDecodeError:
            return []

    @skills.setter
    def skills(self, value: list[str]) -> None:
        self.skills_json = json.dumps(value)

    def compute_hash(self) -> str:
        payload = "|".join(
            [
                self.title,
                self.company,
                self.location,
                self.description_text,
                self.apply_url,
            ]
        )
        return hashlib.sha256(payload.encode()).hexdigest()


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    polish_instructions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    drafts: Mapped[list["Draft"]] = relationship(back_populates="template")


class Draft(Base):
    __tablename__ = "drafts"
    __table_args__ = (
        UniqueConstraint("job_id", "template_id", name="uq_draft_job_template"),
        Index("ix_drafts_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    job: Mapped[Job] = relationship(back_populates="drafts")
    template: Mapped[Template] = relationship(back_populates="drafts")
    revisions: Mapped[list["Revision"]] = relationship(
        back_populates="draft", cascade="all, delete-orphan"
    )


class Revision(Base):
    __tablename__ = "revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[int] = mapped_column(ForeignKey("drafts.id"), nullable=False, index=True)
    requirement: Mapped[str] = mapped_column(Text, nullable=False, default="")
    before: Mapped[str] = mapped_column(Text, nullable=False, default="")
    after: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    draft: Mapped[Draft] = relationship(back_populates="revisions")


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"
    __table_args__ = (Index("ix_scrape_runs_started", "started_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_created: Mapped[int] = mapped_column(Integer, default=0)
    jobs_updated: Mapped[int] = mapped_column(Integer, default=0)
    jobs_archived: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped[Source] = relationship(back_populates="scrape_runs")


class BrandProfile(Base):
    """Singleton brand voice used in prompt packs and template polish."""

    __tablename__ = "brand_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    tone: Mapped[str] = mapped_column(String(255), nullable=False, default="professional, clear")
    voice_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    banned_words: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hashtag_policy: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cta_preference: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
