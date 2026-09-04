"""Centralized application settings loaded from environment variables."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


EnvironmentName = Literal["development", "test", "production"]

# Resolve .env from project layout, not process cwd (start.bat / uvicorn cwd varies).
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Application settings. Prefer env vars / .env over hard-coded values."""

    model_config = SettingsConfigDict(
        env_file=(
            _BACKEND_DIR / ".env",
            _PROJECT_ROOT / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="AI Engineering Copilot", alias="APP_NAME")
    app_env: EnvironmentName = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    # NoDecode: allow comma-separated origins instead of JSON array in .env
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        alias="CORS_ORIGINS",
    )
    database_url: str = Field(
        default="postgresql+psycopg://aec:aec@localhost:5432/aec",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    jwt_secret_key: str = Field(
        default="change-me-in-development-use-long-random-string",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=1440,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    admin_enabled: bool = Field(default=True, alias="ADMIN_ENABLED")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin123456", alias="ADMIN_PASSWORD")
    admin_session_secret: str | None = Field(default=None, alias="ADMIN_SESSION_SECRET")

    llm_enabled: bool = Field(default=True, alias="LLM_ENABLED")
    llm_provider: str = Field(default="openai_compatible", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_timeout_seconds: int = Field(default=90, alias="LLM_TIMEOUT_SECONDS")

    def is_llm_configured(self) -> bool:
        return bool(self.llm_enabled and (self.llm_api_key or "").strip())

    @property
    def resolved_admin_session_secret(self) -> str:
        """Prefer ADMIN_SESSION_SECRET; fall back to JWT_SECRET_KEY."""
        if self.admin_session_secret:
            return self.admin_session_secret
        return self.jwt_secret_key

    def is_admin_password_weak(self) -> bool:
        """Detect empty / placeholder admin passwords unsafe for production."""
        password = (self.admin_password or "").strip()
        if not password:
            return True
        weak = {
            "admin",
            "password",
            "123456",
            "change-me",
            "change-me-in-development-use-long-random-string",
        }
        return password.lower() in weak

    def should_mount_admin(self) -> bool:
        if not self.admin_enabled:
            return False
        if self.app_env == "production" and self.is_admin_password_weak():
            return False
        return True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Accept comma-separated origins from env, e.g. http://a,http://b."""
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return items
        return value


def get_settings() -> Settings:
    """Load settings from env / .env on each call (picks up .env edits without restart)."""
    return Settings()
