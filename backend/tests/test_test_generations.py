"""Test generation API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas.code_generation import CodeGenerationFile, CodeGenerationResult
from app.schemas.test_generation import CaseItem, SuiteFileItem, SuiteGenerationResult
from app.services.llm import factory as llm_factory
from tests.ai_job_helpers import post_ai_job


class _FakeTestProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str):
        raise NotImplementedError

    def plan_technical(self, context: str):
        raise NotImplementedError

    def generate_code(self, context: str) -> CodeGenerationResult:
        raise NotImplementedError

    def generate_tests(self, context: str) -> SuiteGenerationResult:
        return SuiteGenerationResult(
            summary="Login API test suite",
            testing_strategy="Unit tests with mocked DB",
            test_cases=[
                CaseItem(
                    name="login success",
                    type="unit",
                    description="Valid credentials",
                    steps=["POST login"],
                    expected="200 + token",
                ),
            ],
            test_files=[
                SuiteFileItem(
                    path="backend/tests/test_login.py",
                    language="python",
                    description="Login tests",
                    content="def test_login(): pass",
                ),
            ],
            fixtures_and_mocks=["mock user repo"],
            coverage_notes=["covers happy path"],
            risks=["flaky timing"],
            open_questions=["need e2e?"],
        )


class _FakeFailTestProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str):
        raise NotImplementedError

    def plan_technical(self, context: str):
        raise NotImplementedError

    def generate_code(self, context: str) -> CodeGenerationResult:
        raise NotImplementedError

    def generate_tests(self, context: str) -> SuiteGenerationResult:
        raise RuntimeError("test upstream error")


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
        json={"name": "TG Demo"},
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


def test_create_test_generation_target_only(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeTestProvider())
    token = _register_login(client, "tg-target@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/test-generations",
        headers={"Authorization": f"Bearer {token}"},
        payload={"target_description": "用户登录 API 单元测试"},
    )
    assert body["status"] == "succeeded"
    assert body["result_json"]["summary"]


def test_create_test_generation_from_code(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeTestProvider())
    token = _register_login(client, "tg-code@example.com")
    project_id = _create_project(client, token)
    code_id = _create_succeeded_code_gen(client, token, project_id)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/test-generations",
        headers={"Authorization": f"Bearer {token}"},
        payload={
            "target_description": "为登录 API 生成 pytest",
            "code_generation_id": code_id,
        },
    )
    assert body["code_generation_id"] == code_id
    assert body["status"] == "succeeded"


def test_create_test_generation_invalid_code(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeTestProvider())
    token = _register_login(client, "tg-bad@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/test-generations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "target_description": "测试某功能",
            "code_generation_id": "00000000-0000-0000-0000-000000000099",
        },
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == "invalid_code_generation"


def test_create_test_generation_empty_target(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeTestProvider())
    token = _register_login(client, "tg-empty@example.com")
    project_id = _create_project(client, token)

    bad = client.post(
        f"/api/v1/projects/{project_id}/test-generations",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_description": "   "},
    )
    assert bad.status_code == 422


def test_create_test_generation_llm_failure(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeFailTestProvider())
    token = _register_login(client, "tg-fail@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/test-generations",
        headers={"Authorization": f"Bearer {token}"},
        payload={"target_description": "列表分页测试"},
    )
    assert body["status"] == "failed"


def test_test_generation_isolation(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeTestProvider())
    token_a = _register_login(client, "tg-a@example.com")
    token_b = _register_login(client, "tg-b@example.com")
    project_a = _create_project(client, token_a)

    created = client.post(
        f"/api/v1/projects/{project_a}/test-generations",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"target_description": "A 的测试目标"},
    )
    gen_id = created.json()["id"]

    assert client.get(
        f"/api/v1/projects/{project_a}/test-generations",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404

    assert client.get(
        f"/api/v1/projects/{project_a}/test-generations/{gen_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    ).status_code == 404
