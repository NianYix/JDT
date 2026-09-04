"""Read-only project repository endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.repo import RepoFileContent, RepoTreeResponse
from app.services.ai_job import require_owned_project
from app.services import repo_service

router = APIRouter(prefix="/projects/{project_id}/repo", tags=["repo"])


@router.get("/tree", response_model=RepoTreeResponse)
def get_repo_tree(
    project_id: UUID,
    max_depth: int | None = Query(default=None, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RepoTreeResponse:
    project = require_owned_project(db, current_user, project_id)
    return repo_service.list_tree(project, max_depth=max_depth)


@router.get("/file", response_model=RepoFileContent)
def get_repo_file(
    project_id: UUID,
    path: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RepoFileContent:
    project = require_owned_project(db, current_user, project_id)
    return repo_service.read_file(project, path)
