"""Project API tests."""

from fastapi.testclient import TestClient


def _register_login(client: TestClient, email: str) -> str:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "display_name": email.split("@")[0],
        },
    )
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    ).json()["access_token"]


def test_project_crud_and_isolation(client: TestClient) -> None:
    token_a = _register_login(client, "owner-a@example.com")
    token_b = _register_login(client, "owner-b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    created = client.post(
        "/api/v1/projects",
        headers=headers_a,
        json={
            "name": "Alpha",
            "description": "demo",
            "repo_path": "D:/repos/alpha",
        },
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    listed_a = client.get("/api/v1/projects", headers=headers_a)
    assert listed_a.status_code == 200
    assert listed_a.json()["total"] == 1
    assert listed_a.json()["items"][0]["name"] == "Alpha"

    listed_b = client.get("/api/v1/projects", headers=headers_b)
    assert listed_b.status_code == 200
    assert listed_b.json()["total"] == 0

    forbidden = client.get(f"/api/v1/projects/{project_id}", headers=headers_b)
    assert forbidden.status_code == 404
    assert forbidden.json()["code"] == "project_not_found"

    updated = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=headers_a,
        json={"name": "Alpha-2"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Alpha-2"

    deleted = client.delete(f"/api/v1/projects/{project_id}", headers=headers_a)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/projects/{project_id}", headers=headers_a).status_code == 404


def test_projects_require_auth(client: TestClient) -> None:
    assert client.get("/api/v1/projects").status_code == 401
