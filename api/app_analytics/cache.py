from collections import defaultdict
from threading import Lock

from django.conf import settings
from django.utils import timezone

from app_analytics.models import Resource
from app_analytics.tasks import (
    track_feature_evaluation,
    track_feature_evaluation_influxdb,
    track_request,
)


class APIUsageCache:
    def __init__(self) -> None:
        self._cache: dict[tuple[Resource, str, str], int] = {}
        self._last_flushed_at = timezone.now()
        self._lock = Lock()

    def _flush(self) -> None:
        for key, value in self._cache.items():
            track_request.run_in_thread(
                kwargs={
                    "resource": key[0].value,
                    "host": key[1],
                    "environment_key": key[2],
                    "count": value,
                }
            )

        self._cache = {}
        self._last_flushed_at = timezone.now()

    def track_request(
        self,
        resource: Resource,
        host: str,
        environment_key: str,
    ) -> None:
        key = (resource, host, environment_key)
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
    def __init__(self):  # type: ignore[no-untyped-def]
        self._cache = {}
        self._last_flushed_at = timezone.now()
        self._lock = Lock()

    def _flush(self):  # type: ignore[no-untyped-def]
        evaluation_data = defaultdict(dict)  # type: ignore[var-annotated]
        for (environment_id, feature_name), eval_count in self._cache.items():
            evaluation_data[environment_id][feature_name] = eval_count

        for environment_id, feature_evaluations in evaluation_data.items():
            if settings.USE_POSTGRES_FOR_ANALYTICS:
                track_feature_evaluation.delay(
                    kwargs={
                        "environment_id": environment_id,
                        "feature_evaluations": feature_evaluations,
                    }
                )

            elif settings.INFLUXDB_TOKEN:
                track_feature_evaluation_influxdb.delay(
                    kwargs={
                        "environment_id": environment_id,
                        "feature_evaluations": feature_evaluations,
                    }
                )

        self._cache = {}
        self._last_flushed_at = timezone.now()

    def track_feature_evaluation(  # type: ignore[no-untyped-def]
        self, environment_id: int, feature_name: str, evaluation_count: int
    ):
        key = (environment_id, feature_name)
        with self._lock:
            if key not in self._cache:
                self._cache[key] = evaluation_count
            else:
                self._cache[key] += evaluation_count

            if (
                timezone.now() - self._last_flushed_at
            ).seconds > settings.FEATURE_EVALUATION_CACHE_SECONDS:
                self._flush()  # type: ignore[no-untyped-call]
