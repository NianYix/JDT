"""Shared project ownership checks for AI workflows."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository


def require_owned_project(db: Session, owner: User, project_id: UUID) -> Project:
    project = ProjectRepository(db).get_by_id_for_owner(project_id, owner.id)
    if project is None:
        raise AppError("Project not found", code="project_not_found", status_code=404)
    return project
