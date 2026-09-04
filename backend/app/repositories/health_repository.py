"""Health-related data access placeholders.

No business tables exist yet. This class keeps the Repository layer wired so
future connectivity checks can live here without reshaping callers.
"""


class HealthRepository:
    """Data-access boundary for health checks (currently a no-op)."""

    def ping(self) -> bool:
        """Reserved for a future SELECT 1 / Redis PING; always True for now."""
        return True
