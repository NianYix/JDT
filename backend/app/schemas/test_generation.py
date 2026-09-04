"""Test generation schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ai_job import AiJobStatusLiteral, normalize_selected_files_in_schema


TestGenerationStatus = AiJobStatusLiteral


class CaseItem(BaseModel):
    name: str = ""
    type: str = ""
    description: str = ""
    steps: list[str] = Field(default_factory=list)
    expected: str = ""


class SuiteFileItem(BaseModel):
    path: str = ""
    language: str = ""
    description: str = ""
    content: str = ""


class SuiteGenerationResult(BaseModel):
    summary: str = ""
    testing_strategy: str = ""
    test_cases: list[CaseItem] = Field(default_factory=list)
    test_files: list[SuiteFileItem] = Field(default_factory=list)
    fixtures_and_mocks: list[str] = Field(default_factory=list)
    coverage_notes: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class TestGenerationCreate(BaseModel):
    code_generation_id: UUID | None = None
    target_description: str = Field(..., min_length=1, max_length=100_000)
    context_text: str | None = Field(default=None, max_length=100_000)
    selected_files: list[str] = Field(default_factory=list)

    @field_validator("target_description")
    @classmethod
    def strip_target_description(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("target_description must not be empty")
        return stripped

    @field_validator("selected_files")
    @classmethod
    def normalize_files(cls, value: list[str] | None) -> list[str]:
        return normalize_selected_files_in_schema(value)


class TestGenerationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    code_generation_id: UUID | None
    created_by: UUID
    target_description: str
    context_text: str | None
    selected_files: list[str] = Field(default_factory=list)
    status: TestGenerationStatus
    result_json: dict[str, Any] | None = None
    model_name: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
