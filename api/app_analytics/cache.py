from app_analytics.tasks import track_request
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
