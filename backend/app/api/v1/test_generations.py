"""Test generation HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.test_generation import TestGenerationCreate, TestGenerationPublic
from app.services.test_generation_service import TestGenerationService

router = APIRouter(prefix="/projects/{project_id}/test-generations", tags=["test-generations"])


@router.post("", response_model=TestGenerationPublic, status_code=201)
def create_test_generation(
    project_id: UUID,
    payload: TestGenerationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestGenerationPublic:
    return TestGenerationService(db).create(
        current_user,
        project_id,
        payload,
        background_tasks,
    )


@router.get("", response_model=PageResponse[TestGenerationPublic])
def list_test_generations(
    project_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PageResponse[TestGenerationPublic]:
    return TestGenerationService(db).list_for_project(
        current_user,
        project_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{generation_id}", response_model=TestGenerationPublic)
def get_test_generation(
    project_id: UUID,
    generation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestGenerationPublic:
    return TestGenerationService(db).get_for_project(
        current_user,
        project_id,
        generation_id,
    )
