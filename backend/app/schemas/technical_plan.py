"""Technical plan schemas."""

from datetime import datetime
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.ai_job import AiJobStatusLiteral, normalize_selected_files_in_schema


PlanStatus = AiJobStatusLiteral


class TechnicalPlanModule(BaseModel):
    name: str = ""
    responsibility: str = ""


class TechnicalPlanResult(BaseModel):
    summary: str = ""
    architecture_overview: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    modules: list[TechnicalPlanModule] = Field(default_factory=list)
    api_outline: list[str] = Field(default_factory=list)
    data_model_outline: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risks_and_mitigations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class TechnicalPlanCreate(BaseModel):
    requirement_analysis_id: UUID | None = None
    context_text: str | None = Field(default=None, max_length=100_000)
    selected_files: list[str] = Field(default_factory=list)

    @field_validator("selected_files")
    @classmethod
    def normalize_files(cls, value: list[str] | None) -> list[str]:
        return normalize_selected_files_in_schema(value)

    @model_validator(mode="after")
    def require_input(self) -> Self:
        has_analysis = self.requirement_analysis_id is not None
        has_text = bool((self.context_text or "").strip())
        has_files = bool(self.selected_files)
        if not has_analysis and not has_text and not has_files:
            raise ValueError(
                "requirement_analysis_id, non-empty context_text, or selected_files is required"
            )
        return self


class TechnicalPlanPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    requirement_analysis_id: UUID | None
    created_by: UUID
    context_text: str | None
    selected_files: list[str] = Field(default_factory=list)
    status: PlanStatus
    result_json: dict[str, Any] | None = None
    model_name: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
