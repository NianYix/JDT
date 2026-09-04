"""Technical plan HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.technical_plan import TechnicalPlanCreate, TechnicalPlanPublic
from app.services.technical_plan_service import TechnicalPlanService

router = APIRouter(prefix="/projects/{project_id}/technical-plans", tags=["technical-plans"])


@router.post("", response_model=TechnicalPlanPublic, status_code=201)
def create_plan(
    project_id: UUID,
    payload: TechnicalPlanCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TechnicalPlanPublic:
    return TechnicalPlanService(db).create(
        current_user,
        project_id,
        payload,
        background_tasks,
    )


@router.get("", response_model=PageResponse[TechnicalPlanPublic])
def list_plans(
    project_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PageResponse[TechnicalPlanPublic]:
    return TechnicalPlanService(db).list_for_project(
        current_user,
        project_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{plan_id}", response_model=TechnicalPlanPublic)
def get_plan(
    project_id: UUID,
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TechnicalPlanPublic:
    return TechnicalPlanService(db).get_for_project(
        current_user,
        project_id,
        plan_id,
    )
