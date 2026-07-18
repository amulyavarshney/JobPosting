from fastapi import APIRouter

from app.config import get_settings
from app.schemas import SettingsRead, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsRead)
def get_settings_view():
    settings = get_settings()
    configured = bool(
        settings.ollama_base_url
        or settings.openai_api_key
        or settings.anthropic_api_key
        or settings.gemini_api_key
    )
    return SettingsRead(
        environment=settings.environment,
        ollama_base_url=settings.ollama_base_url,
        openai_api_key_configured=bool(settings.openai_api_key),
        anthropic_api_key_configured=bool(settings.anthropic_api_key),
        gemini_api_key_configured=bool(settings.gemini_api_key),
        llm_providers_enabled=configured,
        api_key_required=settings.api_key_required,
        scheduler_enabled=settings.enable_scheduler,
        archive_missing_jobs=settings.archive_missing_jobs,
    )


@router.patch("", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate):
    """Runtime overlay for optional LLM settings (prefer .env for production)."""
    settings = get_settings()
    if payload.ollama_base_url is not None:
        settings.ollama_base_url = payload.ollama_base_url or None
    if payload.openai_api_key is not None:
        settings.openai_api_key = payload.openai_api_key or None
    if payload.anthropic_api_key is not None:
        settings.anthropic_api_key = payload.anthropic_api_key or None
    if payload.gemini_api_key is not None:
        settings.gemini_api_key = payload.gemini_api_key or None
    return get_settings_view()
