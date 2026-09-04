"""Auth API tests."""

from fastapi.testclient import TestClient


def test_register_and_login(client: TestClient) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "password": "password123",
            "display_name": "Alice",
        },
    )
    assert register.status_code == 201
    body = register.json()
    assert body["email"] == "alice@example.com"
    assert "hashed_password" not in body

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    token_body = login.json()
    assert token_body["token_type"] == "bearer"
    assert token_body["access_token"]
    assert token_body["user"]["email"] == "alice@example.com"


def test_register_duplicate_email(client: TestClient) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "password123",
        "display_name": "Dup",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    again = client.post("/api/v1/auth/register", json=payload)
    assert again.status_code == 409
    assert again.json()["code"] == "email_already_registered"


def test_login_invalid_credentials(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@example.com",
            "password": "password123",
            "display_name": "Bob",
        },
    )
    bad = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "wrong-password"},
    )
    assert bad.status_code == 401
    assert bad.json()["code"] == "invalid_credentials"


def test_me_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "carol@example.com",
            "password": "password123",
            "display_name": "Carol",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "password123"},
    ).json()["access_token"]

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "carol@example.com"
