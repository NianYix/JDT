"""Requirement analysis HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.requirement_analysis import (
    RequirementAnalysisCreate,
    RequirementAnalysisPublic,
)
from app.services.requirement_analysis_service import RequirementAnalysisService

router = APIRouter(prefix="/projects/{project_id}/requirement-analyses", tags=["requirement-analyses"])


@router.post("", response_model=RequirementAnalysisPublic, status_code=201)
def create_analysis(
    project_id: UUID,
    payload: RequirementAnalysisCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementAnalysisPublic:
    return RequirementAnalysisService(db).create(
        current_user,
        project_id,
        payload,
        background_tasks,
    )


@router.get("", response_model=PageResponse[RequirementAnalysisPublic])
def list_analyses(
    project_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PageResponse[RequirementAnalysisPublic]:
    return RequirementAnalysisService(db).list_for_project(
        current_user,
        project_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{analysis_id}", response_model=RequirementAnalysisPublic)
def get_analysis(
    project_id: UUID,
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementAnalysisPublic:
    return RequirementAnalysisService(db).get_for_project(
        current_user,
        project_id,
        analysis_id,
    )
