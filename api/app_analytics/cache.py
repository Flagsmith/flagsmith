from threading import Lock

from django.conf import settings
from django.utils import timezone

from app_analytics.mappers import (
    map_feature_evaluation_cache_to_track_feature_evaluations_by_environment_kwargs,
)
from app_analytics.models import Resource
from app_analytics.tasks import (
    track_feature_evaluations_by_environment,
    track_request,
)
from app_analytics.types import (
    APIUsageCacheKey,
    FeatureEvaluationCacheKey,
    Labels,
)


class APIUsageCache:
    def __init__(self) -> None:
        self._cache: dict[APIUsageCacheKey, int] = {}
        self._last_flushed_at = timezone.now()
        self._lock = Lock()

    def _flush(self) -> None:
        for key, value in self._cache.items():
            track_request.run_in_thread(
                kwargs={
                    "resource": key.resource.value,
                    "host": key.host,
                    "environment_key": key.environment_key,
                    "count": value,
                    "labels": dict(key.labels),
                }
            )

        self._cache = {}
        self._last_flushed_at = timezone.now()

    def track_request(
        self,
        resource: Resource,
        host: str,
        environment_key: str,
        labels: Labels,
    ) -> None:
        key = APIUsageCacheKey(
            resource=resource,
            host=host,
            environment_key=environment_key,
            labels=tuple(sorted(labels.items())),
        )
        with self._lock:
            if key not in self._cache:
                self._cache[key] = 1
            else:
                self._cache[key] += 1
            if (
                timezone.now() - self._last_flushed_at
            ).seconds > settings.API_USAGE_CACHE_SECONDS:
                self._flush()


class FeatureEvaluationCache:
    def __init__(self) -> None:
        self._cache: dict[FeatureEvaluationCacheKey, int] = {}
        self._last_flushed_at = timezone.now()
        self._lock = Lock()

    def _flush(self) -> None:
        for kwargs in map_feature_evaluation_cache_to_track_feature_evaluations_by_environment_kwargs(
            self._cache
        ):
            track_feature_evaluations_by_environment.delay(kwargs=dict(kwargs))

        self._cache = {}
        self._last_flushed_at = timezone.now()

    def track_feature_evaluation(
        self,
        environment_id: int,
        feature_name: str,
        evaluation_count: int,
        labels: Labels,
    ) -> None:
        key = FeatureEvaluationCacheKey(
            feature_name=feature_name,
            environment_id=environment_id,
            labels=tuple((sorted(labels.items()))),
        )
        with self._lock:
            if key not in self._cache:
                self._cache[key] = evaluation_count
            else:
                self._cache[key] += evaluation_count

            if (
                timezone.now() - self._last_flushed_at
            ).seconds > settings.FEATURE_EVALUATION_CACHE_SECONDS:
                self._flush()
