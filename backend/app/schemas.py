from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SourceBase(BaseModel):
    name: str
    kind: str = Field(description="greenhouse|lever|ashby|workday|custom")
    base_url: str
    enabled: bool = True
    scrape_interval_minutes: int = Field(
        default=0, ge=0, description="0 = manual only; otherwise auto-scrape interval"
    )


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: str | None = None
    kind: str | None = None
    base_url: str | None = None
    enabled: bool | None = None
    scrape_interval_minutes: int | None = Field(default=None, ge=0)


class SourceRead(SourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_scraped_at: datetime | None = None
    last_error: str | None = None
    last_run_status: str = "never"
    created_at: datetime
    updated_at: datetime | None = None


class JobBase(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    employment_type: str = ""
    salary_text: str = ""
    description_html: str = ""
    description_text: str = ""
    skills: list[str] = Field(default_factory=list)
    apply_url: str = ""
    external_id: str | None = None
    posted_at: datetime | None = None
    needs_manual_fill: bool = False
    raw_url: str = ""
    status: str = "active"


class JobCreate(JobBase):
    source_id: int | None = None


class JobUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    salary_text: str | None = None
    description_html: str | None = None
    description_text: str | None = None
    skills: list[str] | None = None
    apply_url: str | None = None
    needs_manual_fill: bool | None = None
    status: str | None = None
    content_changed: bool | None = None


class JobRead(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int | None
    content_hash: str
    scraped_at: datetime
    last_seen_at: datetime | None = None
    content_changed: bool = False


class PaginatedJobs(BaseModel):
    items: list[JobRead]
    total: int
    page: int
    page_size: int
    pages: int


class TemplateBase(BaseModel):
    channel: str
    name: str
    body: str
    polish_instructions: str = ""
    is_default: bool = False


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    channel: str | None = None
    name: str | None = None
    body: str | None = None
    polish_instructions: str | None = None
    is_default: bool | None = None


class TemplateRead(TemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TemplatePreviewRequest(BaseModel):
    job_id: int
    body: str | None = None


class TemplatePreviewResponse(BaseModel):
    content: str


class DraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    template_id: int
    channel: str
    content: str
    status: str
    created_at: datetime
    updated_at: datetime


class DraftUpdate(BaseModel):
    content: str | None = None
    status: str | None = None


class GenerateDraftsRequest(BaseModel):
    job_id: int
    template_ids: list[int]
    overwrite_reviewed: bool = False


class BulkGenerateRequest(BaseModel):
    job_ids: list[int] = Field(min_length=1)
    template_ids: list[int] = Field(min_length=1)
    overwrite_reviewed: bool = False


class BulkGenerateResponse(BaseModel):
    drafts: list[DraftRead]
    jobs_processed: int


class PromptPackRequest(BaseModel):
    requirement: str = ""


class PromptPackResponse(BaseModel):
    prompt: str
    draft_id: int
    channel: str


class ImportResultRequest(BaseModel):
    content: str
    requirement: str = ""


class ScrapeResponse(BaseModel):
    source_id: int
    run_id: int | None = None
    jobs_found: int
    jobs_created: int
    jobs_updated: int
    jobs_archived: int = 0
    status: str = "success"
    error_message: str | None = None
    duration_ms: float = 0.0


class ScrapeAllResponse(BaseModel):
    results: list[ScrapeResponse]
    sources_scraped: int


class ScrapeRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    source_name: str | None = None
    status: str
    jobs_found: int
    jobs_created: int
    jobs_updated: int
    jobs_archived: int
    error_message: str | None
    duration_ms: float
    started_at: datetime
    finished_at: datetime | None


class DraftQueueItem(BaseModel):
    id: int
    job_id: int
    channel: str
    status: str
    job_title: str = ""
    company: str = ""
    updated_at: datetime


class RevisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    draft_id: int
    requirement: str
    before: str
    after: str
    source: str
    created_at: datetime


class ExportResponse(BaseModel):
    draft_id: int
    channel: str
    content: str
    job_title: str
    company: str
    format: str = "text"
    markdown: str | None = None


class BrandProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_name: str
    tone: str
    voice_notes: str
    banned_words: str
    hashtag_policy: str
    cta_preference: str
    updated_at: datetime | None = None


class BrandProfileUpdate(BaseModel):
    organization_name: str | None = None
    tone: str | None = None
    voice_notes: str | None = None
    banned_words: str | None = None
    hashtag_policy: str | None = None
    cta_preference: str | None = None


class SettingsRead(BaseModel):
    environment: str
    ollama_base_url: str | None = None
    openai_api_key_configured: bool = False
    anthropic_api_key_configured: bool = False
    gemini_api_key_configured: bool = False
    llm_providers_enabled: bool = False
    api_key_required: bool = False
    scheduler_enabled: bool = True
    archive_missing_jobs: bool = True


class DashboardStats(BaseModel):
    sources_total: int
    sources_enabled: int
    jobs_active: int
    jobs_archived: int
    jobs_needs_manual_fill: int
    jobs_changed: int
    drafts_total: int
    drafts_reviewed: int
    drafts_pending: int = 0
    scrape_runs_24h: int
    scrape_failures_24h: int
    templates_total: int
    recent_jobs: list[JobRead]
    recent_runs: list[ScrapeRunRead]
    pending_drafts: list[DraftQueueItem] = Field(default_factory=list)
