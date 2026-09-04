"""LLM provider abstractions."""

from typing import Protocol

from app.schemas.development_metric import MetricsReportResult
from app.schemas.debug_session import DebugAnalysisResult
from app.schemas.code_review import ReviewResult
from app.schemas.code_generation import CodeGenerationResult
from app.schemas.requirement_analysis import RequirementAnalysisResult
from app.schemas.technical_plan import TechnicalPlanResult
from app.schemas.test_generation import SuiteGenerationResult


class LLMProvider(Protocol):
    """Contract for AI engineering LLM capabilities."""

    @property
    def model_name(self) -> str: ...

    def analyze_requirements(self, source_text: str) -> RequirementAnalysisResult: ...

    def plan_technical(self, context: str) -> TechnicalPlanResult: ...

    def generate_code(self, context: str) -> CodeGenerationResult: ...

    def generate_tests(self, context: str) -> SuiteGenerationResult: ...

    def review_code(self, context: str) -> ReviewResult: ...

    def debug_issue(self, context: str) -> DebugAnalysisResult: ...

    def generate_metrics(self, context: str) -> MetricsReportResult: ...
