"""Requirement analysis use cases (async AI job)."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.user import User
from app.repositories.requirement_analysis_repository import RequirementAnalysisRepository
from app.schemas.common import PageResponse
from app.schemas.requirement_analysis import (
    RequirementAnalysisCreate,
    RequirementAnalysisPublic,
)
from app.services.ai_job import (
    AiJobStatus,
    require_owned_project,
    safe_error_message,
    schedule_ai_job,
    with_worker_session,
)
from app.services.llm import factory as llm_factory
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class RequirementAnalysisService:
    def __init__(
        self,
        db: Session,
        *,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self._db = db
        self._analyses = RequirementAnalysisRepository(db)
        self._llm_provider = llm_provider

    def create(
        self,
        owner: User,
        project_id: UUID,
        payload: RequirementAnalysisCreate,
        background_tasks: BackgroundTasks,
    ) -> RequirementAnalysisPublic:
        require_owned_project(self._db, owner, project_id)
        row = self._analyses.create(
            project_id=project_id,
            created_by=owner.id,
            source_text=payload.source_text,
            status=AiJobStatus.PENDING,
        )
        provider = self._llm_provider
        record_id = row.id

        def _job() -> None:
            RequirementAnalysisService._execute(record_id, project_id, provider)

        schedule_ai_job(background_tasks, _job)
        return RequirementAnalysisPublic.model_validate(row)

    @staticmethod
    def _execute(
        record_id: UUID,
        project_id: UUID,
        llm_provider: LLMProvider | None,
    ) -> None:
        def _run(db: Session) -> None:
            repo = RequirementAnalysisRepository(db)
            row = repo.get_by_id_for_project(record_id, project_id)
            if row is None or row.status not in {AiJobStatus.PENDING, AiJobStatus.RUNNING}:
                return
            row.status = AiJobStatus.RUNNING
            repo.update(row)
            model_name = None
            try:
                provider = llm_provider or llm_factory.get_llm_provider()
                model_name = provider.model_name
                result = provider.analyze_requirements(row.source_text)
                row.status = AiJobStatus.SUCCEEDED
                row.result_json = result.model_dump()
                row.model_name = model_name
                row.error_message = None
            except Exception as exc:  # noqa: BLE001
                logger.exception("Requirement analysis LLM failed: %s", exc)
                row.status = AiJobStatus.FAILED
                row.result_json = None
                row.model_name = model_name
                row.error_message = safe_error_message(exc)
            repo.update(row)

        with_worker_session(_run)

    def list_for_project(
        self,
        owner: User,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> PageResponse[RequirementAnalysisPublic]:
        require_owned_project(self._db, owner, project_id)
        items, total = self._analyses.list_by_project(
            project_id,
            page=page,
            page_size=page_size,
        )
        return PageResponse(
            items=[RequirementAnalysisPublic.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_for_project(
        self,
        owner: User,
        project_id: UUID,
        analysis_id: UUID,
    ) -> RequirementAnalysisPublic:
        require_owned_project(self._db, owner, project_id)
        row = self._analyses.get_by_id_for_project(analysis_id, project_id)
        if row is None:
            raise AppError(
                "Requirement analysis not found",
                code="requirement_analysis_not_found",
                status_code=404,
            )
        return RequirementAnalysisPublic.model_validate(row)
