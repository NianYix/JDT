"""Technical planning use cases (async AI job)."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_analysis_repository import RequirementAnalysisRepository
from app.repositories.technical_plan_repository import TechnicalPlanRepository
from app.schemas.common import PageResponse
from app.schemas.technical_plan import TechnicalPlanCreate, TechnicalPlanPublic
from app.services import repo_service
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


class TechnicalPlanService:
    def __init__(
        self,
        db: Session,
        *,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self._db = db
        self._analyses = RequirementAnalysisRepository(db)
        self._plans = TechnicalPlanRepository(db)
        self._llm_provider = llm_provider

    @staticmethod
    def _build_context(
        db: Session,
        project_id: UUID,
        *,
        requirement_analysis_id: UUID | None,
        context_text: str | None,
        selected_files: list[str],
    ) -> str:
        sections: list[str] = []
        analyses = RequirementAnalysisRepository(db)

        if requirement_analysis_id is not None:
            analysis = analyses.get_by_id_for_project(requirement_analysis_id, project_id)
            if analysis is None or analysis.status != AiJobStatus.SUCCEEDED:
                raise AppError(
                    "Requirement analysis is missing or not succeeded",
                    code="invalid_requirement_analysis",
                    status_code=400,
                )
            if analysis.result_json:
                sections.append(
                    "--- Requirement Analysis (JSON) ---\n"
                    + json.dumps(analysis.result_json, ensure_ascii=False, indent=2)
                )
            else:
                sections.append(
                    "--- Requirement Analysis (source) ---\n" + analysis.source_text
                )

        if context_text:
            sections.append("--- Additional Context ---\n" + context_text)

        if selected_files:
            project = ProjectRepository(db).get_by_id(project_id)
            if project is None:
                raise AppError("Project not found", code="project_not_found", status_code=404)
            sections.append(repo_service.load_selected_files_for_prompt(project, selected_files))

        if not sections:
            raise AppError(
                "requirement_analysis_id, context_text, or selected_files is required",
                code="invalid_input",
                status_code=400,
            )
        return "\n\n".join(sections)

    def create(
        self,
        owner: User,
        project_id: UUID,
        payload: TechnicalPlanCreate,
        background_tasks: BackgroundTasks,
    ) -> TechnicalPlanPublic:
        project = require_owned_project(self._db, owner, project_id)
        selected = list(payload.selected_files or [])
        if selected:
            selected = repo_service.validate_selected_paths(project, selected)

        analysis_id = payload.requirement_analysis_id
        context_text = (payload.context_text or "").strip() or None
        if analysis_id is not None:
            analysis = self._analyses.get_by_id_for_project(analysis_id, project_id)
            if analysis is None or analysis.status != AiJobStatus.SUCCEEDED:
                raise AppError(
                    "Requirement analysis is missing or not succeeded",
                    code="invalid_requirement_analysis",
                    status_code=400,
                )
        if analysis_id is None and not context_text and not selected:
            raise AppError(
                "requirement_analysis_id, context_text, or selected_files is required",
                code="invalid_input",
                status_code=400,
            )

        row = self._plans.create(
            project_id=project_id,
            created_by=owner.id,
            requirement_analysis_id=analysis_id,
            context_text=context_text,
            selected_files_json=selected or None,
            status=AiJobStatus.PENDING,
        )
        provider = self._llm_provider
        record_id = row.id

        def _job() -> None:
            TechnicalPlanService._execute(record_id, project_id, provider)

        schedule_ai_job(background_tasks, _job)
        return TechnicalPlanPublic.model_validate(row)

    @staticmethod
    def _execute(
        record_id: UUID,
        project_id: UUID,
        llm_provider: LLMProvider | None,
    ) -> None:
        def _run(db: Session) -> None:
            repo = TechnicalPlanRepository(db)
            row = repo.get_by_id_for_project(record_id, project_id)
            if row is None or row.status not in {AiJobStatus.PENDING, AiJobStatus.RUNNING}:
                return
            row.status = AiJobStatus.RUNNING
            repo.update(row)
            model_name = None
            try:
                provider = llm_provider or llm_factory.get_llm_provider()
                model_name = provider.model_name
                llm_context = TechnicalPlanService._build_context(
                    db,
                    project_id,
                    requirement_analysis_id=row.requirement_analysis_id,
                    context_text=row.context_text,
                    selected_files=row.selected_files,
                )
                result = provider.plan_technical(llm_context)
                row.status = AiJobStatus.SUCCEEDED
                row.result_json = result.model_dump()
                row.model_name = model_name
                row.error_message = None
            except Exception as exc:  # noqa: BLE001
                logger.exception("Technical planning LLM failed: %s", exc)
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
    ) -> PageResponse[TechnicalPlanPublic]:
        require_owned_project(self._db, owner, project_id)
        items, total = self._plans.list_by_project(
            project_id,
            page=page,
            page_size=page_size,
        )
        return PageResponse(
            items=[TechnicalPlanPublic.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_for_project(
        self,
        owner: User,
        project_id: UUID,
        plan_id: UUID,
    ) -> TechnicalPlanPublic:
        require_owned_project(self._db, owner, project_id)
        row = self._plans.get_by_id_for_project(plan_id, project_id)
        if row is None:
            raise AppError(
                "Technical plan not found",
                code="technical_plan_not_found",
                status_code=404,
            )
        return TechnicalPlanPublic.model_validate(row)
