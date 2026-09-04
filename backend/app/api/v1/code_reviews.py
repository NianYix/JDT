"""Code review HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.code_review import CodeReviewCreate, CodeReviewPublic
from app.schemas.common import PageResponse
from app.services.code_review_service import CodeReviewService

router = APIRouter(prefix="/projects/{project_id}/code-reviews", tags=["code-reviews"])


@router.post("", response_model=CodeReviewPublic, status_code=201)
def create_review(
    project_id: UUID,
    payload: CodeReviewCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CodeReviewPublic:
    return CodeReviewService(db).create(
        current_user,
        project_id,
        payload,
        background_tasks,
    )


@router.get("", response_model=PageResponse[CodeReviewPublic])
def list_reviews(
    project_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PageResponse[CodeReviewPublic]:
    return CodeReviewService(db).list_for_project(
        current_user,
        project_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{review_id}", response_model=CodeReviewPublic)
def get_review(
    project_id: UUID,
    review_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CodeReviewPublic:
    return CodeReviewService(db).get_for_project(
        current_user,
        project_id,
        review_id,
    )
