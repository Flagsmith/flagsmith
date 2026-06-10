from __future__ import annotations

from functools import lru_cache

from django.conf import settings
from redis.cluster import RedisCluster

INGESTION_ENVIRONMENT_KEY_PREFIX = "experimentation:environment_keys:"


SOCKET_TIMEOUT = 1


@lru_cache(maxsize=1)
def _get_client() -> RedisCluster:
    return RedisCluster.from_url(  # type: ignore[no-untyped-call,no-any-return]
        settings.INGESTION_REDIS_URL,
        socket_timeout=SOCKET_TIMEOUT,
        socket_keepalive=True,
    )


def set_environment_key(environment_api_key: str) -> None:
    key = f"{INGESTION_ENVIRONMENT_KEY_PREFIX}{environment_api_key}"
    _get_client().set(key, "")


def delete_environment_key(environment_api_key: str) -> None:
    key = f"{INGESTION_ENVIRONMENT_KEY_PREFIX}{environment_api_key}"
    _get_client().delete(key)
