"""Health check response schema."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Process liveness payload (no DB/Redis probe in this phase)."""

    status: str = Field(description="ok when the process is alive")
    environment: str = Field(description="Active APP_ENV value")
    app_name: str = Field(description="Application display name")
    llm_configured: bool = Field(
        description="True when LLM_ENABLED and LLM_API_KEY are set",
    )
