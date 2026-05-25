from __future__ import annotations

from functools import lru_cache

import structlog
from django.conf import settings
from redis.cluster import RedisCluster
from redis.exceptions import RedisError

INGESTION_ENVIRONMENT_KEY_PREFIX = "experimentation:environment_keys:"

logger = structlog.get_logger("experimentation")


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
    try:
        _get_client().set(key, "")
    except RedisError as exc:
        logger.exception(
            "ingestion_sync.environment_key.failed",
            action="set",
            exc_info=exc,
        )
        return
    logger.info("ingestion_sync.environment_key.set")


def delete_environment_key(environment_api_key: str) -> None:
    key = f"{INGESTION_ENVIRONMENT_KEY_PREFIX}{environment_api_key}"
    try:
        _get_client().delete(key)
    except RedisError as exc:
        logger.exception(
            "ingestion_sync.environment_key.failed",
            action="delete",
            exc_info=exc,
        )
        return
    logger.info("ingestion_sync.environment_key.deleted")
