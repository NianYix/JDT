"""LLM provider factory."""

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.services.llm.base import LLMProvider
from app.services.llm.openai_provider import OpenAICompatibleProvider


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    if not settings.is_llm_configured():
        raise AppError(
            "LLM is not configured. Set LLM_API_KEY (and LLM_ENABLED=true).",
            code="llm_not_configured",
            status_code=503,
        )

    provider = (settings.llm_provider or "").strip().lower()
    if provider in {"openai_compatible", "openai"}:
        return OpenAICompatibleProvider(
            api_key=settings.llm_api_key.strip(),
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
        )

    raise AppError(
        f"Unsupported LLM_PROVIDER: {settings.llm_provider}",
        code="llm_not_configured",
        status_code=503,
    )
