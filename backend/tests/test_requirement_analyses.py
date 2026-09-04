"""Requirement analysis API tests (Mock LLM)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.schemas.requirement_analysis import RequirementAnalysisResult
from app.services.llm import factory as llm_factory
from tests.ai_job_helpers import post_ai_job


class _FakeSuccessProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str) -> RequirementAnalysisResult:
        return RequirementAnalysisResult(
            summary=f"Summary of: {source_text[:40]}",
            goals=["Ship MVP"],
            stakeholders=["Product", "Engineering"],
            functional_requirements=["User can login"],
            non_functional_requirements=["p99 < 200ms"],
            assumptions=["Single tenant"],
            risks=["Scope creep"],
            open_questions=["Mobile support?"],
        )


class _FakeFailProvider:
    model_name = "fake-model"

    def analyze_requirements(self, source_text: str) -> RequirementAnalysisResult:
        raise RuntimeError("upstream timeout")


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
        json={"name": "RA Demo", "description": "d", "repo_path": None},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_analysis_success(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeSuccessProvider())
    token = _register_login(client, "ra-ok@example.com")
    project_id = _create_project(client, token)
    headers = {"Authorization": f"Bearer {token}"}

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/requirement-analyses",
        headers=headers,
        payload={"source_text": "我们需要一个登录与项目管理系统"},
    )
    assert body["status"] == "succeeded"
    assert body["result_json"]["summary"]
    assert body["model_name"] == "fake-model"

    listed = client.get(
        f"/api/v1/projects/{project_id}/requirement-analyses",
        headers=headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    detail = client.get(
        f"/api/v1/projects/{project_id}/requirement-analyses/{body['id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == body["id"]


def test_create_analysis_llm_failure_persists_failed(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeFailProvider())
    token = _register_login(client, "ra-fail@example.com")
    project_id = _create_project(client, token)

    body = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/requirement-analyses",
        headers={"Authorization": f"Bearer {token}"},
        payload={"source_text": "任意需求"},
    )
    assert body["status"] == "failed"
    assert "timeout" in (body["error_message"] or "").lower()


def test_create_analysis_requires_llm_config(client: TestClient, monkeypatch) -> None:
    def _raise(_settings=None):
        from app.core.exceptions import AppError

        raise AppError("LLM is not configured", code="llm_not_configured", status_code=503)

    monkeypatch.setattr(llm_factory, "get_llm_provider", _raise)
    token = _register_login(client, "ra-no-llm@example.com")
    project_id = _create_project(client, token)

    final = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/requirement-analyses",
        headers={"Authorization": f"Bearer {token}"},
        payload={"source_text": "任意需求"},
    )
    assert final["status"] == "failed"
    assert "llm" in (final["error_message"] or "").lower() or "not configured" in (
        final["error_message"] or ""
    ).lower()


def test_analysis_isolation(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _FakeSuccessProvider())
    token_a = _register_login(client, "ra-a@example.com")
    token_b = _register_login(client, "ra-b@example.com")
    project_a = _create_project(client, token_a)

    created = client.post(
        f"/api/v1/projects/{project_a}/requirement-analyses",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"source_text": "A 的需求"},
    )
    assert created.status_code == 201
    analysis_id = created.json()["id"]

    forbidden_list = client.get(
        f"/api/v1/projects/{project_a}/requirement-analyses",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert forbidden_list.status_code == 404

    forbidden_detail = client.get(
        f"/api/v1/projects/{project_a}/requirement-analyses/{analysis_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert forbidden_detail.status_code == 404
