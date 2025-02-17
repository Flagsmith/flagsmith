import typing

from django.apps import apps
from django.conf import settings
from django.core.cache import caches

if typing.TYPE_CHECKING:
    from django.db.models import QuerySet

    from segments.models import Segment

project_segments_cache = caches[settings.PROJECT_SEGMENTS_CACHE_LOCATION]


def get_project_segments_from_cache(project_id: int) -> "QuerySet[Segment]":
    Segment = apps.get_model("segments", "Segment")

    segments = project_segments_cache.get(project_id)
    if not segments:
        # This is optimised to account for rules nested one levels deep (since we
        # don't support anything above that from the UI at the moment). Anything
        # past that will require additional queries / thought on how to optimise.
        segments = Segment.live_objects.filter(project_id=project_id).prefetch_related(
            "rules",
            "rules__conditions",
            "rules__rules",
            "rules__rules__conditions",
            "rules__rules__rules",
        )

        project_segments_cache.set(
            project_id, segments, timeout=settings.CACHE_PROJECT_SEGMENTS_SECONDS
        )

    return segments  # type: ignore[no-any-return]
