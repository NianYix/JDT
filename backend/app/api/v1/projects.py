"""Project HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.project import ProjectCreate, ProjectPublic, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectPublic, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectPublic:
    return ProjectService(db).create(current_user, payload)


@router.get("", response_model=PageResponse[ProjectPublic])
def list_projects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PageResponse[ProjectPublic]:
    return ProjectService(db).list_mine(current_user, page=page, page_size=page_size)


@router.get("/{project_id}", response_model=ProjectPublic)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectPublic:
    return ProjectService(db).get_mine(current_user, project_id)


@router.patch("/{project_id}", response_model=ProjectPublic)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectPublic:
    return ProjectService(db).update_mine(current_user, project_id, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    ProjectService(db).delete_mine(current_user, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
