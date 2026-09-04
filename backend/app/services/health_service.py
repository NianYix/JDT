"""Health check use-case orchestration."""

from app.core.config import Settings, get_settings
from app.repositories.health_repository import HealthRepository
from app.schemas.health import HealthResponse


class HealthService:
    """Compose health status without FastAPI request objects."""

    def __init__(
        self,
        repository: HealthRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository or HealthRepository()
        self._settings = settings or get_settings()

    def get_health(self) -> HealthResponse:
        """Return process liveness. Repository ping is reserved for later probes."""
        _ = self._repository.ping()
        return HealthResponse(
            status="ok",
            environment=self._settings.app_env,
            app_name=self._settings.app_name,
            llm_configured=self._settings.is_llm_configured(),
        )
