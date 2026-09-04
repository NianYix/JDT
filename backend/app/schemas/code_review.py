"""Code review schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ai_job import AiJobStatusLiteral, normalize_selected_files_in_schema


ReviewStatus = AiJobStatusLiteral


class IssueItem(BaseModel):
    severity: str = ""
    location: str = ""
    category: str = ""
    description: str = ""
    suggestion: str = ""


class FixSuggestion(BaseModel):
    path: str = ""
    description: str = ""
    content: str = ""


class ReviewResult(BaseModel):
    summary: str = ""
    overall_assessment: str = ""
    issues: list[IssueItem] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    security_notes: list[str] = Field(default_factory=list)
    performance_notes: list[str] = Field(default_factory=list)
    maintainability_notes: list[str] = Field(default_factory=list)
    suggested_fixes: list[FixSuggestion] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class CodeReviewCreate(BaseModel):
    code_generation_id: UUID | None = None
    review_scope: str = Field(..., min_length=1, max_length=100_000)
    context_text: str | None = Field(default=None, max_length=100_000)
    selected_files: list[str] = Field(default_factory=list)

    @field_validator("review_scope")
    @classmethod
    def strip_review_scope(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("review_scope must not be empty")
        return stripped

    @field_validator("selected_files")
    @classmethod
    def normalize_files(cls, value: list[str] | None) -> list[str]:
        return normalize_selected_files_in_schema(value)


class CodeReviewPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    code_generation_id: UUID | None
    created_by: UUID
    review_scope: str
    context_text: str | None
    selected_files: list[str] = Field(default_factory=list)
    status: ReviewStatus
    result_json: dict[str, Any] | None = None
    model_name: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
