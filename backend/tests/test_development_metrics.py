"""Development metrics API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas.code_generation import CodeGenerationResult
from app.schemas.code_review import ReviewResult
from app.schemas.debug_session import DebugAnalysisResult
from app.schemas.development_metric import MetricsReportResult, QualityIndicatorItem, WorkflowCoverageItem
from app.schemas.requirement_analysis import RequirementAnalysisResult
from app.schemas.technical_plan import TechnicalPlanResult
from app.schemas.test_generation import SuiteGenerationResult
from app.services.llm import factory as llm_factory
from tests.ai_job_helpers import post_ai_job


class _FakeMetricsProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str) -> RequirementAnalysisResult:
        raise NotImplementedError

    def plan_technical(self, context: str) -> TechnicalPlanResult:
        raise NotImplementedError

    def generate_code(self, context: str) -> CodeGenerationResult:
        raise NotImplementedError

    def generate_tests(self, context: str) -> SuiteGenerationResult:
        raise NotImplementedError

    def review_code(self, context: str) -> ReviewResult:
        raise NotImplementedError

    def debug_issue(self, context: str) -> DebugAnalysisResult:
        raise NotImplementedError

    def generate_metrics(self, context: str) -> MetricsReportResult:
        assert "Workflow Statistics" in context
        assert "requirement_analysis" in context
        return MetricsReportResult(
            summary="Project health report",
            overall_health="Moderate — testing stage weak",
            workflow_coverage=[
                WorkflowCoverageItem(
                    stage="requirement_analysis",
                    status="covered",
                    notes="Has succeeded records",
                ),
            ],
            quality_indicators=[
                QualityIndicatorItem(
                    name="AI workflow adoption",
                    assessment="Partial",
                    evidence="Some stages unused",
                ),
            ],
            velocity_indicators=["Regular analysis activity"],
            risk_indicators=["Low test generation count"],
            recommendations=["Run automated testing"],
            open_questions=["Need CI integration later?"],
        )


class _FakeFailMetricsProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str) -> RequirementAnalysisResult:
        raise NotImplementedError

    def plan_technical(self, context: str) -> TechnicalPlanResult:
        raise NotImplementedError

    def generate_code(self, context: str) -> CodeGenerationResult:
        raise NotImplementedError

    def generate_tests(self, context: str) -> SuiteGenerationResult:
        raise NotImplementedError

    def review_code(self, context: str) -> ReviewResult:
        raise NotImplementedError

    def debug_issue(self, context: str) -> DebugAnalysisResult:
        raise NotImplementedError

    def generate_metrics(self, context: str) -> MetricsReportResult:
        raise RuntimeError("metrics upstream error")


def _register_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": email.split("@")[0]},
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    ).json()["access_token"]


def _create_project(client: TestClient, token: str) -> str:
    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "DM Demo"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_succeeded_analysis(client: TestClient, token: str, project_id: str) -> None:
    from app.services.llm import factory as ra_factory

    class _RA:
        model_name = "fake"

        def analyze_requirements(self, t: str) -> RequirementAnalysisResult:
            return RequirementAnalysisResult(summary="req summary ok")

        def plan_technical(self, context: str) -> TechnicalPlanResult:
            raise NotImplementedError

        def generate_code(self, context: str) -> CodeGenerationResult:
            raise NotImplementedError

        def generate_tests(self, context: str) -> SuiteGenerationResult:
            raise NotImplementedError

        def review_code(self, context: str) -> ReviewResult:
            raise NotImplementedError

        def debug_issue(self, context: str) -> DebugAnalysisResult:
            raise NotImplementedError

        def generate_metrics(self, context: str) -> MetricsReportResult:
            raise NotImplementedError

    original = ra_factory.get_llm_provider
    ra_factory.get_llm_provider = lambda settings=None: _RA()
    try:
        final = post_ai_job(
            client,
            collection_url=f"/api/v1/projects/{project_id}/requirement-analyses",
            headers={"Authorization": f"Bearer {token}"},
            payload={"source_text": "我们需要用户系统"},
        )
    finally:
        ra_factory.get_llm_provider = original
    assert final["status"] == "succeeded"


def test_create_metrics_empty_project(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeMetricsProvider())
    token = _register_login(client, "dm-empty@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/development-metrics",
        headers={"Authorization": f"Bearer {token}"},
        payload={"metrics_focus": "评估研发健康度"},
    )
    assert body["status"] == "succeeded"
    assert body["result_json"]["summary"]


def test_create_metrics_with_workflow_data(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeMetricsProvider())
    token = _register_login(client, "dm-data@example.com")
    project_id = _create_project(client, token)
    _create_succeeded_analysis(client, token, project_id)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/development-metrics",
        headers={"Authorization": f"Bearer {token}"},
        payload={"metrics_focus": "基于现有 AI 工作流评估质量"},
    )
    assert body["status"] == "succeeded"


def test_create_metrics_empty_focus(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeMetricsProvider())
    token = _register_login(client, "dm-bad@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/development-metrics",
        headers={"Authorization": f"Bearer {token}"},
        json={"metrics_focus": "   "},
    )
    assert bad.status_code == 422


def test_create_metrics_llm_failure(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeFailMetricsProvider())
    token = _register_login(client, "dm-fail@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/development-metrics",
        headers={"Authorization": f"Bearer {token}"},
        payload={"metrics_focus": "季度研发回顾"},
    )
    assert body["status"] == "failed"


def test_metrics_isolation(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeMetricsProvider())
    token_a = _register_login(client, "dm-a@example.com")
    token_b = _register_login(client, "dm-b@example.com")
    project_a = _create_project(client, token_a)

    created = client.post(
        f"/api/v1/projects/{project_a}/development-metrics",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"metrics_focus": "A 的度量"},
    )
    metric_id = created.json()["id"]

    assert client.get(
        f"/api/v1/projects/{project_a}/development-metrics",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404

    assert client.get(
        f"/api/v1/projects/{project_a}/development-metrics/{metric_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404
