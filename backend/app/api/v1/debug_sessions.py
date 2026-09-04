"""Debug session HTTP endpoints."""

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.debug_session import DebugSessionCreate, DebugSessionPublic
from app.services.debug_session_service import DebugSessionService

router = APIRouter(prefix="/projects/{project_id}/debug-sessions", tags=["debug-sessions"])


@router.post("", response_model=DebugSessionPublic, status_code=201)
def create_debug_session(
    project_id: UUID,
    payload: DebugSessionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DebugSessionPublic:
    return DebugSessionService(db).create(
        current_user,
        project_id,
        payload,
        background_tasks,
    )


@router.get("", response_model=PageResponse[DebugSessionPublic])
def list_debug_sessions(
    project_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PageResponse[DebugSessionPublic]:
    return DebugSessionService(db).list_for_project(
        current_user,
        project_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{session_id}", response_model=DebugSessionPublic)
def get_debug_session(
    project_id: UUID,
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DebugSessionPublic:
    return DebugSessionService(db).get_for_project(
        current_user,
        project_id,
        session_id,
    )
