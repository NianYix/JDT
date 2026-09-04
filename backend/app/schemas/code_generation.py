"""Code generation schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ai_job import AiJobStatusLiteral, normalize_selected_files_in_schema


GenerationStatus = AiJobStatusLiteral


class CodeGenerationFile(BaseModel):
    path: str = ""
    language: str = ""
    description: str = ""
    content: str = ""


class CodeGenerationResult(BaseModel):
    summary: str = ""
    approach: str = ""
    files: list[CodeGenerationFile] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    implementation_steps: list[str] = Field(default_factory=list)
    testing_notes: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class CodeGenerationCreate(BaseModel):
    technical_plan_id: UUID | None = None
    task_description: str = Field(..., min_length=1, max_length=100_000)
    context_text: str | None = Field(default=None, max_length=100_000)
    selected_files: list[str] = Field(default_factory=list)

    @field_validator("task_description")
    @classmethod
    def strip_task_description(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("task_description must not be empty")
        return stripped

    @field_validator("selected_files")
    @classmethod
    def normalize_files(cls, value: list[str] | None) -> list[str]:
        return normalize_selected_files_in_schema(value)


class CodeGenerationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    technical_plan_id: UUID | None
    created_by: UUID
    task_description: str
    context_text: str | None
    selected_files: list[str] = Field(default_factory=list)
    status: GenerationStatus
    result_json: dict[str, Any] | None = None
    model_name: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
