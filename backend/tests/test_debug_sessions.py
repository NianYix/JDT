"""Debug session API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas.code_generation import CodeGenerationResult
from app.schemas.code_review import ReviewResult
from app.schemas.debug_session import DebugAnalysisResult, DebugFixItem, LikelyCauseItem
from app.schemas.test_generation import SuiteGenerationResult
from app.services.llm import factory as llm_factory
from tests.ai_job_helpers import post_ai_job


class _FakeDebugProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str):
        raise NotImplementedError

    def plan_technical(self, context: str):
        raise NotImplementedError

    def generate_code(self, context: str) -> CodeGenerationResult:
        raise NotImplementedError

    def generate_tests(self, context: str) -> SuiteGenerationResult:
        raise NotImplementedError

    def review_code(self, context: str) -> ReviewResult:
        raise NotImplementedError

    def debug_issue(self, context: str) -> DebugAnalysisResult:
        return DebugAnalysisResult(
            summary="Login 500 error",
            root_cause_analysis="Null user after token decode",
            likely_causes=[
                LikelyCauseItem(
                    hypothesis="Expired token not rejected",
                    confidence="high",
                    evidence="401 missing in middleware",
                ),
            ],
            debugging_steps=["Reproduce with curl", "Check logs"],
            fix_suggestions=[
                DebugFixItem(description="Validate token expiry", content="if expired: raise 401"),
            ],
            verification_steps=["Run pytest auth"],
            prevention_notes=["Add integration test"],
            open_questions=["Need refresh token?"],
        )


class _FakeFailDebugProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str):
        raise NotImplementedError

    def plan_technical(self, context: str):
        raise NotImplementedError

    def generate_code(self, context: str) -> CodeGenerationResult:
        raise NotImplementedError

    def generate_tests(self, context: str) -> SuiteGenerationResult:
        raise NotImplementedError

    def review_code(self, context: str) -> ReviewResult:
        raise NotImplementedError

    def debug_issue(self, context: str) -> DebugAnalysisResult:
        raise RuntimeError("debug upstream error")


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
        json={"name": "DB Demo"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_succeeded_review(client: TestClient, token: str, project_id: str) -> str:
    from app.services.llm import factory as cr_factory

    class _CR:
        model_name = "fake"

        def analyze_requirements(self, source_text: str):
            raise NotImplementedError

        def plan_technical(self, context: str):
            raise NotImplementedError

        def generate_code(self, context: str) -> CodeGenerationResult:
            raise NotImplementedError

        def generate_tests(self, context: str) -> SuiteGenerationResult:
            raise NotImplementedError

        def review_code(self, context: str) -> ReviewResult:
            return ReviewResult(summary="review ok")

        def debug_issue(self, context: str) -> DebugAnalysisResult:
            raise NotImplementedError

    original = cr_factory.get_llm_provider
    cr_factory.get_llm_provider = lambda settings=None: _CR()
    try:
        final = post_ai_job(
            client,
            collection_url=f"/api/v1/projects/{project_id}/code-reviews",
            headers={"Authorization": f"Bearer {token}"},
            payload={"review_scope": "审查登录模块"},
        )
    finally:
        cr_factory.get_llm_provider = original
    assert final["status"] == "succeeded"
    return final["id"]


def test_create_debug_problem_only(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeDebugProvider())
    token = _register_login(client, "db-prob@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/debug-sessions",
        headers={"Authorization": f"Bearer {token}"},
        payload={"problem_description": "登录接口返回 500"},
    )
    assert body["status"] == "succeeded"
    assert body["result_json"]["summary"]


def test_create_debug_with_review(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeDebugProvider())
    token = _register_login(client, "db-rev@example.com")
    project_id = _create_project(client, token)
    review_id = _create_succeeded_review(client, token, project_id)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/debug-sessions",
        headers={"Authorization": f"Bearer {token}"},
        payload={
            "problem_description": "审查指出的安全问题如何复现",
            "code_review_id": review_id,
        },
    )
    assert body["code_review_id"] == review_id
    assert body["status"] == "succeeded"


def test_create_debug_invalid_review(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeDebugProvider())
    token = _register_login(client, "db-bad@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/debug-sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "problem_description": "某错误",
            "code_review_id": "00000000-0000-0000-0000-000000000099",
        },
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == "invalid_code_review"


def test_create_debug_empty_problem(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeDebugProvider())
    token = _register_login(client, "db-empty@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/debug-sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"problem_description": "   "},
    )
    assert bad.status_code == 422


def test_create_debug_llm_failure(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeFailDebugProvider())
    token = _register_login(client, "db-fail@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/debug-sessions",
        headers={"Authorization": f"Bearer {token}"},
        payload={"problem_description": "分页偶发超时"},
    )
    assert body["status"] == "failed"


def test_debug_session_isolation(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeDebugProvider())
    token_a = _register_login(client, "db-a@example.com")
    token_b = _register_login(client, "db-b@example.com")
    project_a = _create_project(client, token_a)

    created = client.post(
        f"/api/v1/projects/{project_a}/debug-sessions",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"problem_description": "A 的问题"},
    )
    session_id = created.json()["id"]

    assert client.get(
        f"/api/v1/projects/{project_a}/debug-sessions",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404

    assert client.get(
        f"/api/v1/projects/{project_a}/debug-sessions/{session_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404
