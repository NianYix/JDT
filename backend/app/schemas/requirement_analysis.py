"""Requirement analysis schemas."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


AnalysisStatus = Literal["pending", "running", "succeeded", "failed"]


class RequirementAnalysisResult(BaseModel):
    summary: str = ""
    goals: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    functional_requirements: list[str] = Field(default_factory=list)
    non_functional_requirements: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class RequirementAnalysisCreate(BaseModel):
    source_text: str = Field(min_length=1, max_length=100_000)


class RequirementAnalysisPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    created_by: UUID
    source_text: str
    status: AnalysisStatus
    result_json: dict[str, Any] | None = None
    model_name: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
