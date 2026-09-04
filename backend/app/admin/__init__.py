"""Mount SQLAdmin console onto the FastAPI application."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from sqladmin import Admin

from app.admin.auth import AdminAuth
from app.admin.views import ProjectAdmin, UserAdmin
from app.core.config import Settings, get_settings
from app.db.session import get_engine

logger = logging.getLogger(__name__)


def setup_admin(app: FastAPI, settings: Settings | None = None) -> Admin | None:
    """Attach /admin when enabled and credentials are acceptable."""
    settings = settings or get_settings()

    if not settings.should_mount_admin():
        if not settings.admin_enabled:
            logger.warning("SQLAdmin disabled: ADMIN_ENABLED=false")
        elif settings.app_env == "production" and settings.is_admin_password_weak():
            logger.warning(
                "SQLAdmin disabled in production: ADMIN_PASSWORD is empty or a weak placeholder"
            )
        else:
            logger.warning("SQLAdmin disabled by configuration")
        return None

    authentication_backend = AdminAuth(secret_key=settings.resolved_admin_session_secret)
    admin = Admin(
        app=app,
        engine=get_engine(),
        authentication_backend=authentication_backend,
        title="AEC Admin",
        base_url="/admin",
    )
    admin.add_view(UserAdmin)
    admin.add_view(ProjectAdmin)
    logger.info("SQLAdmin mounted at /admin")
    return admin
