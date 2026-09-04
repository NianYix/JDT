"""Technical plan API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas.technical_plan import TechnicalPlanModule, TechnicalPlanResult
from app.services.llm import factory as llm_factory
from tests.ai_job_helpers import post_ai_job


class _FakePlanProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str):
        raise NotImplementedError

    def plan_technical(self, context: str) -> TechnicalPlanResult:
        return TechnicalPlanResult(
            summary="Plan for context",
            architecture_overview="Monolith API + React SPA",
            tech_stack=["FastAPI", "PostgreSQL"],
            modules=[
                TechnicalPlanModule(name="Auth", responsibility="JWT login"),
            ],
            api_outline=["POST /api/v1/auth/login"],
            data_model_outline=["users", "projects"],
            milestones=["M1: Auth", "M2: Core API"],
            dependencies=["PostgreSQL"],
            risks_and_mitigations=["LLM cost — cache prompts"],
            open_questions=["Need mobile app?"],
        )


class _FakeFailPlanProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str):
        raise NotImplementedError

    def plan_technical(self, context: str) -> TechnicalPlanResult:
        raise RuntimeError("plan upstream error")


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
        json={"name": "TP Demo"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_succeeded_analysis(client: TestClient, token: str, project_id: str) -> str:
    from app.services.llm import factory as ra_factory
    from app.schemas.requirement_analysis import RequirementAnalysisResult

    class _RA:
        model_name = "fake"
        def analyze_requirements(self, t: str) -> RequirementAnalysisResult:
            return RequirementAnalysisResult(summary="ok summary")
        def plan_technical(self, context: str) -> TechnicalPlanResult:
            raise NotImplementedError

    original = ra_factory.get_llm_provider
    ra_factory.get_llm_provider = lambda settings=None: _RA()
    try:
        final = post_ai_job(
            client,
            collection_url=f"/api/v1/projects/{project_id}/requirement-analyses",
            headers={"Authorization": f"Bearer {token}"},
            payload={"source_text": "我们需要登录和项目管理"},
        )
    finally:
        ra_factory.get_llm_provider = original
    assert final["status"] == "succeeded"
    return final["id"]


def test_create_plan_from_context(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakePlanProvider())
    token = _register_login(client, "tp-ctx@example.com")
    project_id = _create_project(client, token)
    headers = {"Authorization": f"Bearer {token}"}

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/technical-plans",
        headers=headers,
        payload={"context_text": "补充：需要支持多租户"},
    )
    assert body["status"] == "succeeded"
    assert body["result_json"]["summary"]


def test_create_plan_from_analysis(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakePlanProvider())
    token = _register_login(client, "tp-ra@example.com")
    project_id = _create_project(client, token)
    analysis_id = _create_succeeded_analysis(client, token, project_id)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/technical-plans",
        headers={"Authorization": f"Bearer {token}"},
        payload={"requirement_analysis_id": analysis_id},
    )
    assert body["requirement_analysis_id"] == analysis_id
    assert body["status"] == "succeeded"


def test_create_plan_invalid_analysis(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakePlanProvider())
    token = _register_login(client, "tp-bad@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/technical-plans",
        headers={"Authorization": f"Bearer {token}"},
        json={"requirement_analysis_id": "00000000-0000-0000-0000-000000000099"},
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == "invalid_requirement_analysis"


def test_create_plan_llm_failure(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeFailPlanProvider())
    token = _register_login(client, "tp-fail@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/technical-plans",
        headers={"Authorization": f"Bearer {token}"},
        payload={"context_text": "任意上下文"},
    )
    assert body["status"] == "failed"


def test_plan_isolation(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakePlanProvider())
    token_a = _register_login(client, "tp-a@example.com")
    token_b = _register_login(client, "tp-b@example.com")
    project_a = _create_project(client, token_a)

    created = client.post(
        f"/api/v1/projects/{project_a}/technical-plans",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"context_text": "A 的上下文"},
    )
    plan_id = created.json()["id"]

    assert client.get(
        f"/api/v1/projects/{project_a}/technical-plans",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404

    assert client.get(
        f"/api/v1/projects/{project_a}/technical-plans/{plan_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404
