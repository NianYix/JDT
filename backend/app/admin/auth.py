"""SQLAdmin authentication backend (independent from business JWT users)."""

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import get_settings


class AdminAuth(AuthenticationBackend):
    """Validate ADMIN_USERNAME / ADMIN_PASSWORD via session cookie."""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username") or "")
        password = str(form.get("password") or "")
        settings = get_settings()
        if username == settings.admin_username and password == settings.admin_password:
            request.session.update({"admin_authenticated": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("admin_authenticated"))
