"""Read-only repository API tests."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


def _register_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "display_name": email.split("@")[0]},
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    ).json()["access_token"]


def _create_project(client: TestClient, token: str, *, repo_path: str | None) -> str:
    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Repo Demo", "repo_path": repo_path},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_repo_tree_and_file(client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "readme.md").write_text("# demo\n", encoding="utf-8")

    token = _register_login(client, "repo-ok@example.com")
    project_id = _create_project(client, token, repo_path=str(tmp_path))
    headers = {"Authorization": f"Bearer {token}"}

    tree = client.get(f"/api/v1/projects/{project_id}/repo/tree", headers=headers)
    assert tree.status_code == 200
    body = tree.json()
    paths = {e["path"] for e in body["entries"]}
    assert "src" in paths
    assert "src/main.py" in paths
    assert "readme.md" in paths

    file_resp = client.get(
        f"/api/v1/projects/{project_id}/repo/file",
        headers=headers,
        params={"path": "src/main.py"},
    )
    assert file_resp.status_code == 200
    assert "print" in file_resp.json()["content"]


def test_repo_not_configured(client: TestClient) -> None:
    token = _register_login(client, "repo-none@example.com")
    project_id = _create_project(client, token, repo_path=None)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(f"/api/v1/projects/{project_id}/repo/tree", headers=headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == "repo_not_configured"


def test_repo_path_traversal(client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "safe.txt").write_text("ok", encoding="utf-8")
    token = _register_login(client, "repo-trav@example.com")
    project_id = _create_project(client, token, repo_path=str(tmp_path))
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get(
        f"/api/v1/projects/{project_id}/repo/file",
        headers=headers,
        params={"path": "../secret.txt"},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "path_outside_repo"


def test_repo_file_too_large(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.repo_service.MAX_FILE_BYTES", 10)
    (tmp_path / "big.txt").write_text("x" * 50, encoding="utf-8")
    token = _register_login(client, "repo-big@example.com")
    project_id = _create_project(client, token, repo_path=str(tmp_path))
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get(
        f"/api/v1/projects/{project_id}/repo/file",
        headers=headers,
        params={"path": "big.txt"},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "file_too_large"


def test_repo_isolation(client: TestClient, tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    token_a = _register_login(client, "repo-a@example.com")
    token_b = _register_login(client, "repo-b@example.com")
    project_a = _create_project(client, token_a, repo_path=str(tmp_path))

    forbidden = client.get(
        f"/api/v1/projects/{project_a}/repo/tree",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert forbidden.status_code == 404


def test_code_gen_with_selected_files(client: TestClient, tmp_path: Path, monkeypatch) -> None:
    from app.schemas.code_generation import CodeGenerationFile, CodeGenerationResult
    from app.services.llm import factory as llm_factory
    from tests.ai_job_helpers import post_ai_job

    captured: dict[str, str] = {}

    class _Fake:
        model_name = "fake"

        def generate_code(self, context: str) -> CodeGenerationResult:
            captured["context"] = context
            return CodeGenerationResult(
                summary="ok",
                approach="a",
                files=[
                    CodeGenerationFile(
                        path="x.py",
                        language="python",
                        description="d",
                        content="pass",
                    )
                ],
            )

        def analyze_requirements(self, source_text: str):
            raise NotImplementedError

        def plan_technical(self, context: str):
            raise NotImplementedError

        def generate_tests(self, context: str):
            raise NotImplementedError

        def review_code(self, context: str):
            raise NotImplementedError

        def debug_issue(self, context: str):
            raise NotImplementedError

        def generate_metrics(self, context: str):
            raise NotImplementedError

    (tmp_path / "app.py").write_text("VALUE = 42\n", encoding="utf-8")
    monkeypatch.setattr(llm_factory, "get_llm_provider", lambda settings=None: _Fake())
    token = _register_login(client, "repo-cg@example.com")
    project_id = _create_project(client, token, repo_path=str(tmp_path))
    headers = {"Authorization": f"Bearer {token}"}

    final = post_ai_job(
        client,
        collection_url=f"/api/v1/projects/{project_id}/code-generations",
        headers=headers,
        payload={
            "task_description": "refactor app",
            "selected_files": ["app.py"],
        },
    )
    assert final["status"] == "succeeded"
    assert final["selected_files"] == ["app.py"]
    assert "VALUE = 42" in captured["context"]
    assert "--- Repository Files ---" in captured["context"]
