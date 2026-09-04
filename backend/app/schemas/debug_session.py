"""Debug session schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ai_job import AiJobStatusLiteral, normalize_selected_files_in_schema


DebugSessionStatus = AiJobStatusLiteral


class LikelyCauseItem(BaseModel):
    hypothesis: str = ""
    confidence: str = ""
    evidence: str = ""


class DebugFixItem(BaseModel):
    description: str = ""
    content: str = ""


class DebugAnalysisResult(BaseModel):
    summary: str = ""
    root_cause_analysis: str = ""
    likely_causes: list[LikelyCauseItem] = Field(default_factory=list)
    debugging_steps: list[str] = Field(default_factory=list)
    fix_suggestions: list[DebugFixItem] = Field(default_factory=list)
    verification_steps: list[str] = Field(default_factory=list)
    prevention_notes: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class DebugSessionCreate(BaseModel):
    code_review_id: UUID | None = None
    code_generation_id: UUID | None = None
    problem_description: str = Field(..., min_length=1, max_length=100_000)
    context_text: str | None = Field(default=None, max_length=100_000)
    selected_files: list[str] = Field(default_factory=list)

    @field_validator("problem_description")
    @classmethod
    def strip_problem_description(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("problem_description must not be empty")
        return stripped

    @field_validator("selected_files")
    @classmethod
    def normalize_files(cls, value: list[str] | None) -> list[str]:
        return normalize_selected_files_in_schema(value)


class DebugSessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    code_review_id: UUID | None
    code_generation_id: UUID | None
    created_by: UUID
    problem_description: str
    context_text: str | None
    selected_files: list[str] = Field(default_factory=list)
    status: DebugSessionStatus
    result_json: dict[str, Any] | None = None
    model_name: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
