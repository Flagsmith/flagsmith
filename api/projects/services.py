import typing

from django.apps import apps
from django.conf import settings
from django.core.cache import caches
from django.db import connection, transaction

if typing.TYPE_CHECKING:
    from segments.models import Segment

project_segments_cache = caches[settings.PROJECT_SEGMENTS_CACHE_LOCATION]


def get_project_segments_from_cache(project_id: int) -> "list[Segment]":
    """
    Get all segments for a project from cache or database.

    Uses REPEATABLE READ isolation for PostgreSQL to ensure all prefetch
    queries see the same database snapshot, avoiding race conditions
    during concurrent segment updates.
    """
    Segment = apps.get_model("segments", "Segment")

    segments = project_segments_cache.get(project_id)
    if not segments:
        # Use REPEATABLE READ isolation to ensure prefetch queries
        # see a consistent snapshot, preventing race conditions where
        # rules are fetched but their conditions are deleted by a
        # concurrent PATCH before they can be prefetched.
        #
        # Only attempt to set isolation level if we're not already in an
        # atomic block (nested transactions can't change isolation level).
        use_repeatable_read = (
            connection.vendor == "postgresql" and not connection.in_atomic_block
        )
        with transaction.atomic():
            if use_repeatable_read:
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            # This is optimised to account for rules nested one levels deep
            # (since we don't support anything above that from the UI at the
            # moment). Anything past that will require additional queries /
            # thought on how to optimise.
            segments = list(
                Segment.live_objects.filter(project_id=project_id).prefetch_related(
                    "rules",
                    "rules__conditions",
                    "rules__rules",
                    "rules__rules__conditions",
                    "rules__rules__rules",
                )
            )

        project_segments_cache.set(
            project_id, segments, timeout=settings.CACHE_PROJECT_SEGMENTS_SECONDS
        )

    return segments  # type: ignore[no-any-return]
