"""Code review API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas.code_generation import CodeGenerationFile, CodeGenerationResult
from app.schemas.code_review import FixSuggestion, IssueItem, ReviewResult
from app.schemas.test_generation import SuiteGenerationResult
from app.services.llm import factory as llm_factory
from tests.ai_job_helpers import post_ai_job


class _FakeReviewProvider:
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
        return ReviewResult(
            summary="Login API review",
            overall_assessment="Needs minor security hardening",
            issues=[
                IssueItem(
                    severity="major",
                    location="auth.py",
                    category="security",
                    description="Missing rate limit",
                    suggestion="Add throttling",
                ),
            ],
            strengths=["Clear layering"],
            security_notes=["Validate input"],
            performance_notes=[],
            maintainability_notes=["Good naming"],
            suggested_fixes=[
                FixSuggestion(
                    path="auth.py",
                    description="Add rate limit",
                    content="limiter = ...",
                ),
            ],
            open_questions=["Need OAuth?"],
        )


class _FakeFailReviewProvider:
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
        raise RuntimeError("review upstream error")


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
        json={"name": "CR Demo"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _create_succeeded_code_gen(client: TestClient, token: str, project_id: str) -> str:
    from app.services.llm import factory as cg_factory

    class _CG:
        model_name = "fake"

        def analyze_requirements(self, source_text: str):
            raise NotImplementedError

        def plan_technical(self, context: str):
            raise NotImplementedError

        def generate_code(self, context: str) -> CodeGenerationResult:
            return CodeGenerationResult(
                summary="code ok",
                files=[CodeGenerationFile(path="app.py", content="x")],
            )

        def generate_tests(self, context: str) -> SuiteGenerationResult:
            raise NotImplementedError

        def review_code(self, context: str) -> ReviewResult:
            raise NotImplementedError

    original = cg_factory.get_llm_provider
    cg_factory.get_llm_provider = lambda settings=None: _CG()
    try:
        final = post_ai_job(
            client,
            collection_url=f"/api/v1/projects/{project_id}/code-generations",
            headers={"Authorization": f"Bearer {token}"},
            payload={"task_description": "实现登录 API"},
        )
    finally:
        cg_factory.get_llm_provider = original
    assert final["status"] == "succeeded"
    return final["id"]


def test_create_review_scope_only(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeReviewProvider())
    token = _register_login(client, "cr-scope@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/code-reviews",
        headers={"Authorization": f"Bearer {token}"},
        payload={"review_scope": "审查登录 API 实现"},
    )
    assert body["status"] == "succeeded"
    assert body["result_json"]["summary"]


def test_create_review_from_code_gen(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeReviewProvider())
    token = _register_login(client, "cr-code@example.com")
    project_id = _create_project(client, token)
    code_id = _create_succeeded_code_gen(client, token, project_id)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/code-reviews",
        headers={"Authorization": f"Bearer {token}"},
        payload={
            "review_scope": "审查上述编码建议",
            "code_generation_id": code_id,
        },
    )
    assert body["code_generation_id"] == code_id
    assert body["status"] == "succeeded"


def test_create_review_invalid_code_gen(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeReviewProvider())
    token = _register_login(client, "cr-bad@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/code-reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "review_scope": "审查某代码",
            "code_generation_id": "00000000-0000-0000-0000-000000000099",
        },
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == "invalid_code_generation"


def test_create_review_empty_scope(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeReviewProvider())
    token = _register_login(client, "cr-empty@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/code-reviews",
        headers={"Authorization": f"Bearer {token}"},
        json={"review_scope": "   "},
    )
    assert bad.status_code == 422


def test_create_review_llm_failure(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeFailReviewProvider())
    token = _register_login(client, "cr-fail@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/code-reviews",
        headers={"Authorization": f"Bearer {token}"},
        payload={"review_scope": "审查分页实现"},
    )
    assert body["status"] == "failed"


def test_review_isolation(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeReviewProvider())
    token_a = _register_login(client, "cr-a@example.com")
    token_b = _register_login(client, "cr-b@example.com")
    project_a = _create_project(client, token_a)

    created = client.post(
        f"/api/v1/projects/{project_a}/code-reviews",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"review_scope": "A 的审查"},
    )
    review_id = created.json()["id"]

    assert client.get(
        f"/api/v1/projects/{project_a}/code-reviews",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404

    assert client.get(
        f"/api/v1/projects/{project_a}/code-reviews/{review_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404
