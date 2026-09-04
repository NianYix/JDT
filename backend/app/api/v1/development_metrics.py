"""Development metrics HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.development_metric import DevelopmentMetricCreate, DevelopmentMetricPublic
from app.services.development_metric_service import DevelopmentMetricService

router = APIRouter(
    prefix="/projects/{project_id}/development-metrics",
    tags=["development-metrics"],
)


@router.post("", response_model=DevelopmentMetricPublic, status_code=201)
def create_metric(
    project_id: UUID,
    payload: DevelopmentMetricCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DevelopmentMetricPublic:
    return DevelopmentMetricService(db).create(
        current_user,
        project_id,
        payload,
        background_tasks,
    )


@router.get("", response_model=PageResponse[DevelopmentMetricPublic])
def list_metrics(
    project_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PageResponse[DevelopmentMetricPublic]:
    return DevelopmentMetricService(db).list_for_project(
        current_user,
        project_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{metric_id}", response_model=DevelopmentMetricPublic)
def get_metric(
    project_id: UUID,
    metric_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DevelopmentMetricPublic:
    return DevelopmentMetricService(db).get_for_project(
        current_user,
        project_id,
        metric_id,
    )
