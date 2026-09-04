"""Code generation HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.code_generation import CodeGenerationCreate, CodeGenerationPublic
from app.schemas.common import PageResponse
from app.services.code_generation_service import CodeGenerationService

router = APIRouter(prefix="/projects/{project_id}/code-generations", tags=["code-generations"])


@router.post("", response_model=CodeGenerationPublic, status_code=201)
def create_generation(
    project_id: UUID,
    payload: CodeGenerationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CodeGenerationPublic:
    return CodeGenerationService(db).create(
        current_user,
        project_id,
        payload,
        background_tasks,
    )


@router.get("", response_model=PageResponse[CodeGenerationPublic])
def list_generations(
    project_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PageResponse[CodeGenerationPublic]:
    return CodeGenerationService(db).list_for_project(
        current_user,
        project_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{generation_id}", response_model=CodeGenerationPublic)
def get_generation(
    project_id: UUID,
    generation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CodeGenerationPublic:
    return CodeGenerationService(db).get_for_project(
        current_user,
        project_id,
        generation_id,
    )
