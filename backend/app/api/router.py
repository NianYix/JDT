"""Aggregate API routers."""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    code_generations,
    code_reviews,
    debug_sessions,
    development_metrics,
    health,
    projects,
    repo,
    requirement_analyses,
    technical_plans,
    test_generations,
)

api_router = APIRouter()
api_router.include_router(health.router)

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(auth.router)
api_v1.include_router(projects.router)
api_v1.include_router(repo.router)
api_v1.include_router(requirement_analyses.router)
api_v1.include_router(technical_plans.router)
api_v1.include_router(code_generations.router)
api_v1.include_router(test_generations.router)
api_v1.include_router(code_reviews.router)
api_v1.include_router(debug_sessions.router)
api_v1.include_router(development_metrics.router)
api_router.include_router(api_v1)
