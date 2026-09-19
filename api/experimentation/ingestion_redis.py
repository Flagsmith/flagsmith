from functools import lru_cache

from django.conf import settings
from redis.cluster import RedisCluster

SOCKET_TIMEOUT = 1


@lru_cache(maxsize=1)
def get_client() -> RedisCluster:
    """The Redis the ingestion server and the warehouse-delivery service read
    their configuration from and, for the latter, write outcomes to."""
    return RedisCluster.from_url(  # type: ignore[no-any-return]
        settings.INGESTION_REDIS_URL,
        socket_timeout=SOCKET_TIMEOUT,
        socket_keepalive=True,
    )
