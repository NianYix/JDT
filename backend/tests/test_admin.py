"""SQLAdmin smoke tests."""

from fastapi.testclient import TestClient


def test_admin_login_page_available(client: TestClient) -> None:
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_admin_index_requires_auth(client: TestClient) -> None:
    response = client.get("/admin/", follow_redirects=False)
    # Unauthenticated users are redirected to login.
    assert response.status_code in {302, 303, 307, 401}
    if response.status_code in {302, 303, 307}:
        assert "/admin/login" in response.headers.get("location", "")


def test_admin_login_success(client: TestClient) -> None:
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123456"},
        follow_redirects=False,
    )
    assert response.status_code in {302, 303}
    assert "session" in response.headers.get("set-cookie", "").lower() or response.cookies
