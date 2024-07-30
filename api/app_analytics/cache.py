from app_analytics.tasks import track_feature_evaluation, track_request
from app_analytics.track import track_feature_evaluation_influxdb
from django.conf import settings
from django.utils import timezone

CACHE_FLUSH_INTERVAL = 60  # seconds


class APIUsageCache:
    def __init__(self):
        self._cache = {}
        self._last_flushed_at = timezone.now()

    def _flush(self):
        for key, value in self._cache.items():
            track_request.delay(
                kwargs={
                    "resource": key[0],
                    "host": key[1],
                    "environment_key": key[2],
                    "count": value,
                }
            )

        self._cache = {}
        self._last_flushed_at = timezone.now()

    def track_request(self, resource: int, host: str, environment_key: str):
        key = (resource, host, environment_key)
        if key not in self._cache:
            self._cache[key] = 1
        else:
            self._cache[key] += 1
        if (timezone.now() - self._last_flushed_at).seconds > CACHE_FLUSH_INTERVAL:
            self._flush()


class FeatureEvaluationCache:
    def __init__(self):
        self._cache = {}
        self._last_flushed_at = timezone.now()

    def _flush(self):
        evaluation_data = {}
        for (environment_id, feature_name), eval_count in self._cache.items():
            if environment_id in evaluation_data:
                evaluation_data[environment_id][feature_name] = eval_count
            else:
                evaluation_data[environment_id] = {feature_name: eval_count}

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

    def track_feature_evaluation(
        self, environment_id: int, feature_name: str, evaluation_count: int
    ):
        key = (environment_id, feature_name)
        if key not in self._cache:
            self._cache[key] = evaluation_count
        else:
            self._cache[key] += evaluation_count

        if (
            timezone.now() - self._last_flushed_at
        ).seconds > settings.FEATURE_EVALUATION_CACHE_SECONDS:
            self._flush()
