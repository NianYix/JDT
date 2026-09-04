"""Development metrics schemas."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


MetricStatus = Literal["pending", "running", "succeeded", "failed"]


class WorkflowCoverageItem(BaseModel):
    stage: str = ""
    status: str = ""
    notes: str = ""


class QualityIndicatorItem(BaseModel):
    name: str = ""
    assessment: str = ""
    evidence: str = ""


class MetricsReportResult(BaseModel):
    summary: str = ""
    overall_health: str = ""
    workflow_coverage: list[WorkflowCoverageItem] = Field(default_factory=list)
    quality_indicators: list[QualityIndicatorItem] = Field(default_factory=list)
    velocity_indicators: list[str] = Field(default_factory=list)
    risk_indicators: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class DevelopmentMetricCreate(BaseModel):
    metrics_focus: str = Field(..., min_length=1, max_length=100_000)
    context_text: str | None = Field(default=None, max_length=100_000)

    @field_validator("metrics_focus")
    @classmethod
    def strip_metrics_focus(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("metrics_focus must not be empty")
        return stripped


class DevelopmentMetricPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    created_by: UUID
    metrics_focus: str
    context_text: str | None
    status: MetricStatus
    result_json: dict[str, Any] | None = None
    model_name: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
