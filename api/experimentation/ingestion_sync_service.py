from __future__ import annotations

from typing import TYPE_CHECKING

from experimentation.ingestion_redis import get_client

if TYPE_CHECKING:
    from datetime import datetime

INGESTION_ENVIRONMENT_KEY_PREFIX = "experimentation:environment_keys:"
INGESTION_ENVIRONMENT_DESTINATION_PREFIX = "experimentation:environment_destinations:"


def set_ingestion_key(
    key: str,
    *,
    environment_key: str,
    expires_at: datetime | None = None,
) -> None:
    redis_key = f"{INGESTION_ENVIRONMENT_KEY_PREFIX}{key}"
    get_client().set(
        redis_key,
        environment_key,
        exat=int(expires_at.timestamp()) if expires_at is not None else None,
    )


def delete_ingestion_key(key: str) -> None:
    redis_key = f"{INGESTION_ENVIRONMENT_KEY_PREFIX}{key}"
    get_client().delete(redis_key)


def set_ingestion_destination(client_api_key: str, *, topic: str) -> None:
    redis_key = f"{INGESTION_ENVIRONMENT_DESTINATION_PREFIX}{client_api_key}"
    get_client().set(redis_key, topic)


def delete_ingestion_destination(client_api_key: str) -> None:
    redis_key = f"{INGESTION_ENVIRONMENT_DESTINATION_PREFIX}{client_api_key}"
    get_client().delete(redis_key)
