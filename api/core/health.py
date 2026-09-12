import structlog
from django.conf import settings
from django.core.cache import caches
from django.core.cache.backends.db import DatabaseCache
from django.db import DatabaseError
from health_check.backends import (  # type: ignore[import-untyped]
    BaseHealthCheckBackend,
)
from health_check.exceptions import (  # type: ignore[import-untyped]
    ServiceUnavailable,
)

logger = structlog.get_logger("health")

CACHE_HEALTH_CHECK_KEY = "flagsmith_cache_table_health_check"


# `BaseHealthCheckBackend` resolves to `Any` because django-health-check ships
# no type information, so subclassing it trips `disallow_subclassing_any`.
class CacheTablesHealthCheck(BaseHealthCheckBackend):  # type: ignore[misc]
    """
    Readiness check that verifies every database-backed cache is usable.

    Django stores some caches in tables created by the ``createcachetable``
    management command rather than by ORM migrations. If that command fails
    during deployment the tables are missing, yet the application still starts
    because the migrations check passes. This backend reads from each
    ``DatabaseCache`` so a missing or unreadable table fails the readiness
    probe immediately instead of breaking features later.
    """

    critical_service = True

    def check_status(self) -> None:
        for alias in settings.CACHES:
            cache = caches[alias]
            if not isinstance(cache, DatabaseCache):
                # In-memory (LocMemCache) and Redis caches have no database
                # table to verify, so they are skipped.
                continue
            try:
                # A read is enough to surface a missing table: `get()` runs a
                # SELECT that raises `DatabaseError` when the table is absent.
                # We avoid `set()` because `DatabaseCache` swallows write
                # errors (returning `False`), which would hide the failure.
                cache.get(CACHE_HEALTH_CHECK_KEY)
            except DatabaseError as exc:
                logger.exception("cache_table.unavailable", cache__alias=alias)
                self.add_error(
                    ServiceUnavailable(f"Cache table for '{alias}' is unavailable"),
                    exc,
                )
