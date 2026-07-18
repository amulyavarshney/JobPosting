from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "JobPosting"
    app_version: str = "2.0.0"
    environment: str = Field(default="development", description="development|staging|production")

    database_url: str = "sqlite:///./jobposting.db"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_base_url: str = "http://127.0.0.1:8000"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    allowed_hosts: str = "*"

    # Auth — required for write routes when environment=production and api_key is set
    api_key: str | None = None
    require_api_key: bool = False

    http_timeout_seconds: float = 30.0
    http_max_redirects: int = 5
    allow_private_networks: bool = False
    scrape_concurrency: int = 2
    scrape_delay_seconds: float = 0.25

    # Scheduler
    enable_scheduler: bool = True
    scheduler_tick_seconds: int = 60
    archive_missing_jobs: bool = True

    # Rate limits (per IP, sliding window)
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    scrape_rate_limit_requests: int = 10
    scrape_rate_limit_window_seconds: int = 60

    # Docs
    enable_docs: bool | None = None

    # Static SPA (production)
    serve_frontend: bool = True
    frontend_dist: str = "../frontend/dist"

    log_level: str = "INFO"
    log_json: bool = False

    # Optional LLM (not required)
    ollama_base_url: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None

    @field_validator("environment")
    @classmethod
    def normalize_env(cls, v: str) -> str:
        return v.lower().strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def docs_enabled(self) -> bool:
        if self.enable_docs is not None:
            return self.enable_docs
        return not self.is_production

    @property
    def api_key_required(self) -> bool:
        if self.require_api_key:
            return True
        return self.is_production and bool(self.api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
