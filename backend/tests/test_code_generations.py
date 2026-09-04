"""Code generation API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas.code_generation import CodeGenerationFile, CodeGenerationResult
from app.schemas.technical_plan import TechnicalPlanResult
from app.services.llm import factory as llm_factory
from tests.ai_job_helpers import post_ai_job


class _FakeCodeProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str):
        raise NotImplementedError

    def plan_technical(self, context: str) -> TechnicalPlanResult:
        raise NotImplementedError

    def generate_code(self, context: str) -> CodeGenerationResult:
        return CodeGenerationResult(
            summary="Login API implementation",
            approach="FastAPI route + service layer",
            files=[
                CodeGenerationFile(
                    path="backend/app/api/v1/auth.py",
                    language="python",
                    description="Login endpoint",
                    content="def login(): pass",
                ),
            ],
            dependencies=["fastapi"],
            implementation_steps=["Add route", "Add tests"],
            testing_notes=["pytest login flow"],
            risks=["Token expiry"],
            open_questions=["Need refresh token?"],
        )


class _FakeFailCodeProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str):
        raise NotImplementedError

    def plan_technical(self, context: str) -> TechnicalPlanResult:
        raise NotImplementedError

    def generate_code(self, context: str) -> CodeGenerationResult:
        raise RuntimeError("code upstream error")


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
        json={"name": "CG Demo"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_succeeded_plan(client: TestClient, token: str, project_id: str) -> str:
    from app.schemas.requirement_analysis import RequirementAnalysisResult
    from app.services.llm import factory as tp_factory

    class _TP:
        model_name = "fake"

        def analyze_requirements(self, t: str) -> RequirementAnalysisResult:
            return RequirementAnalysisResult(summary="ok")

        def plan_technical(self, context: str) -> TechnicalPlanResult:
            return TechnicalPlanResult(summary="plan ok")

        def generate_code(self, context: str) -> CodeGenerationResult:
            raise NotImplementedError

    original = tp_factory.get_llm_provider
    tp_factory.get_llm_provider = lambda settings=None: _TP()
    try:
        final = post_ai_job(
            client,
            collection_url=f"/api/v1/projects/{project_id}/technical-plans",
            headers={"Authorization": f"Bearer {token}"},
            payload={"context_text": "技术上下文"},
        )
    finally:
        tp_factory.get_llm_provider = original
    assert final["status"] == "succeeded"
    return final["id"]


def test_create_generation_task_only(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeCodeProvider())
    token = _register_login(client, "cg-task@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/code-generations",
        headers={"Authorization": f"Bearer {token}"},
        payload={"task_description": "实现用户登录 API"},
    )
    assert body["status"] == "succeeded"
    assert body["result_json"]["summary"]


def test_create_generation_from_plan(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeCodeProvider())
    token = _register_login(client, "cg-plan@example.com")
    project_id = _create_project(client, token)
    plan_id = _create_succeeded_plan(client, token, project_id)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/code-generations",
        headers={"Authorization": f"Bearer {token}"},
        payload={
            "task_description": "按规划实现认证模块",
            "technical_plan_id": plan_id,
        },
    )
    assert body["technical_plan_id"] == plan_id
    assert body["status"] == "succeeded"


def test_create_generation_invalid_plan(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeCodeProvider())
    token = _register_login(client, "cg-bad@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/code-generations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "task_description": "实现某功能",
            "technical_plan_id": "00000000-0000-0000-0000-000000000099",
        },
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == "invalid_technical_plan"


def test_create_generation_empty_task(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeCodeProvider())
    token = _register_login(client, "cg-empty@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/code-generations",
        headers={"Authorization": f"Bearer {token}"},
        json={"task_description": "   "},
    )
    assert bad.status_code == 422


def test_create_generation_llm_failure(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeFailCodeProvider())
    token = _register_login(client, "cg-fail@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/code-generations",
        headers={"Authorization": f"Bearer {token}"},
        payload={"task_description": "实现列表分页"},
    )
    assert body["status"] == "failed"


def test_generation_isolation(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeCodeProvider())
    token_a = _register_login(client, "cg-a@example.com")
    token_b = _register_login(client, "cg-b@example.com")
    project_a = _create_project(client, token_a)

    created = client.post(
        f"/api/v1/projects/{project_a}/code-generations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"task_description": "A 的任务"},
    )
    gen_id = created.json()["id"]

    assert client.get(
        f"/api/v1/projects/{project_a}/code-generations",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404

    assert client.get(
        f"/api/v1/projects/{project_a}/code-generations/{gen_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404
