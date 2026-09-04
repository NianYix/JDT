"""OpenAI-compatible chat provider for AI engineering workflows."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from app.schemas.code_generation import CodeGenerationResult
from app.schemas.code_review import ReviewResult
from app.schemas.debug_session import DebugAnalysisResult
from app.schemas.development_metric import MetricsReportResult
from app.schemas.requirement_analysis import RequirementAnalysisResult
from app.schemas.technical_plan import TechnicalPlanResult
from app.schemas.test_generation import SuiteGenerationResult

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

SYSTEM_PROMPT = """You are a senior business analyst.
Analyze the user's software requirement text and respond with ONLY valid JSON.
Do not wrap the JSON in markdown fences.
Use exactly these keys:
- summary: string
- goals: string array
- stakeholders: string array
- functional_requirements: string array
- non_functional_requirements: string array
- assumptions: string array
- risks: string array
- open_questions: string array
If information is missing, use an empty string or empty array.
Write content in the same language as the input text.
"""

PLAN_SYSTEM_PROMPT = """You are a senior software architect.
Given requirement context, produce a technical plan as ONLY valid JSON.
Do not wrap the JSON in markdown fences.
Use exactly these keys:
- summary: string
- architecture_overview: string
- tech_stack: string array
- modules: array of objects with keys name (string) and responsibility (string)
- api_outline: string array
- data_model_outline: string array
- milestones: string array
- dependencies: string array
- risks_and_mitigations: string array
- open_questions: string array
If information is missing, use empty string or empty array.
Write content in the same language as the input context.
"""

CODE_SYSTEM_PROMPT = """You are a senior software engineer.
Given a coding task and optional technical context, respond with ONLY valid JSON.
Do not wrap the JSON in markdown fences.
Use exactly these keys:
- summary: string
- approach: string
- files: array of objects with keys path, language, description, content (code body)
- dependencies: string array (packages to add)
- implementation_steps: string array
- testing_notes: string array
- risks: string array
- open_questions: string array
If information is missing, use empty string or empty array.
Write content in the same language as the input context.
"""

TEST_SYSTEM_PROMPT = """You are a senior QA engineer and test architect.
Given a test target and optional code context, respond with ONLY valid JSON.
Do not wrap the JSON in markdown fences.
Use exactly these keys:
- summary: string
- testing_strategy: string
- test_cases: array of objects with keys name, type (unit/integration/e2e), description, steps (string array), expected (string)
- test_files: array of objects with keys path, language, description, content (test code body)
- fixtures_and_mocks: string array
- coverage_notes: string array
- risks: string array
- open_questions: string array
If information is missing, use empty string or empty array.
Write content in the same language as the input context.
"""

REVIEW_SYSTEM_PROMPT = """You are a senior staff engineer performing a thorough code review.
Given review scope and optional code context, respond with ONLY valid JSON.
Do not wrap the JSON in markdown fences.
Use exactly these keys:
- summary: string
- overall_assessment: string
- issues: array of objects with keys severity, location, category, description, suggestion
- strengths: string array
- security_notes: string array
- performance_notes: string array
- maintainability_notes: string array
- suggested_fixes: array of objects with keys path, description, content (optional code snippet)
- open_questions: string array
If information is missing, use empty string or empty array.
Write content in the same language as the input context.
"""

DEBUG_SYSTEM_PROMPT = """You are a senior software engineer specializing in debugging.
Given a problem description and optional code/review context, respond with ONLY valid JSON.
Do not wrap the JSON in markdown fences.
Use exactly these keys:
- summary: string
- root_cause_analysis: string
- likely_causes: array of objects with keys hypothesis, confidence (high/medium/low), evidence
- debugging_steps: string array
- fix_suggestions: array of objects with keys description, content (code or command snippet)
- verification_steps: string array
- prevention_notes: string array
- open_questions: string array
If information is missing, use empty string or empty array.
Write content in the same language as the input context.
"""

METRICS_SYSTEM_PROMPT = """You are a software engineering metrics analyst.
Given metrics focus and platform workflow statistics, respond with ONLY valid JSON.
Do not wrap the JSON in markdown fences.
Use exactly these keys:
- summary: string
- overall_health: string
- workflow_coverage: array of objects with keys stage, status (covered/weak/missing), notes
- quality_indicators: array of objects with keys name, assessment, evidence
- velocity_indicators: string array
- risk_indicators: string array
- recommendations: string array
- open_questions: string array
Cover stages: requirement_analysis, technical_planning, ai_coding, automated_testing,
code_review, ai_debugging, development_metrics when interpreting workflow_coverage.
If information is missing, use empty string or empty array.
Write content in the same language as the input context.
"""


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: int,
    ) -> None:
        self._model = model
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )

    @property
    def model_name(self) -> str:
        return self._model

    def _chat_json(self, system: str, user: str, result_type: type[T]) -> T:
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = (response.choices[0].message.content or "").strip()
        payload = _parse_json_content(content)
        return result_type.model_validate(payload)

    def analyze_requirements(self, source_text: str) -> RequirementAnalysisResult:
        return self._chat_json(SYSTEM_PROMPT, source_text, RequirementAnalysisResult)

    def plan_technical(self, context: str) -> TechnicalPlanResult:
        return self._chat_json(PLAN_SYSTEM_PROMPT, context, TechnicalPlanResult)

    def generate_code(self, context: str) -> CodeGenerationResult:
        return self._chat_json(CODE_SYSTEM_PROMPT, context, CodeGenerationResult)

    def generate_tests(self, context: str) -> SuiteGenerationResult:
        return self._chat_json(TEST_SYSTEM_PROMPT, context, SuiteGenerationResult)

    def review_code(self, context: str) -> ReviewResult:
        return self._chat_json(REVIEW_SYSTEM_PROMPT, context, ReviewResult)

    def debug_issue(self, context: str) -> DebugAnalysisResult:
        return self._chat_json(DEBUG_SYSTEM_PROMPT, context, DebugAnalysisResult)

    def generate_metrics(self, context: str) -> MetricsReportResult:
        return self._chat_json(METRICS_SYSTEM_PROMPT, context, MetricsReportResult)


def _parse_json_content(content: str) -> dict[str, Any]:
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if match:
        data = json.loads(match.group(0))
        if isinstance(data, dict):
            return data

    raise ValueError("LLM response is not valid JSON object")
