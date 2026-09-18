from __future__ import annotations

import json
from functools import lru_cache
from typing import TYPE_CHECKING, cast

import structlog
from django.conf import settings
from redis.cluster import RedisCluster

from core.warehouse_credentials import encrypt_warehouse_credentials
from experimentation.dataclasses import WarehouseDeliveryStatus

if TYPE_CHECKING:
    from datetime import datetime

INGESTION_ENVIRONMENT_KEY_PREFIX = "experimentation:environment_keys:"
INGESTION_ENVIRONMENT_DESTINATION_PREFIX = "experimentation:environment_destinations:"
# Read by the warehouse-delivery service to find the warehouse an environment's
# events go to. The rest of the key is the environment's client API key, the
# same value the ingestion server puts on each Kafka message.
INGESTION_ENVIRONMENT_WAREHOUSE_PREFIX = "experimentation:environment_warehouses:"
# One hash the warehouse-delivery service writes each connection's latest
# outcome into, under the connection id. Emptied by
# apply_warehouse_delivery_statuses once a minute.
WAREHOUSE_DELIVERY_STATUS_KEY = "experimentation:warehouse_delivery_status"

# Returns every field and value of the hash and deletes it in the same step,
# so an outcome the delivery service writes while we are reading is never
# deleted unread.
_POP_HASH_SCRIPT = """
local entries = redis.call('HGETALL', KEYS[1])
redis.call('DEL', KEYS[1])
return entries
"""

SOCKET_TIMEOUT = 1

logger = structlog.get_logger("experimentation")


@lru_cache(maxsize=1)
def _get_client() -> RedisCluster:
    return RedisCluster.from_url(  # type: ignore[no-any-return]
        settings.INGESTION_REDIS_URL,
        socket_timeout=SOCKET_TIMEOUT,
        socket_keepalive=True,
    )


def set_ingestion_key(
    key: str,
    *,
    environment_key: str,
    expires_at: datetime | None = None,
) -> None:
    redis_key = f"{INGESTION_ENVIRONMENT_KEY_PREFIX}{key}"
    _get_client().set(
        redis_key,
        environment_key,
        exat=int(expires_at.timestamp()) if expires_at is not None else None,
    )


def delete_ingestion_key(key: str) -> None:
    redis_key = f"{INGESTION_ENVIRONMENT_KEY_PREFIX}{key}"
    _get_client().delete(redis_key)


def set_ingestion_destination(client_api_key: str, *, topic: str) -> None:
    redis_key = f"{INGESTION_ENVIRONMENT_DESTINATION_PREFIX}{client_api_key}"
    _get_client().set(redis_key, topic)


def delete_ingestion_destination(client_api_key: str) -> None:
    redis_key = f"{INGESTION_ENVIRONMENT_DESTINATION_PREFIX}{client_api_key}"
    _get_client().delete(redis_key)


def set_ingestion_warehouse(
    client_api_key: str,
    *,
    connection_id: int,
    warehouse_type: str,
    config: dict[str, object],
    credentials: dict[str, object] | None,
) -> None:
    """Publishes the warehouse the delivery service should insert the
    environment's events into. Credentials travel as the same Fernet
    ciphertext the database holds, so only a service that has
    WAREHOUSE_CREDENTIALS_SECRET can read them out of Redis."""
    redis_key = f"{INGESTION_ENVIRONMENT_WAREHOUSE_PREFIX}{client_api_key}"
    document = {
        "connection_id": connection_id,
        "warehouse_type": warehouse_type,
        "config": config,
        "credentials": encrypt_warehouse_credentials(credentials)
        if credentials is not None
        else None,
    }
    _get_client().set(redis_key, json.dumps(document))


def delete_ingestion_warehouse(client_api_key: str) -> None:
    redis_key = f"{INGESTION_ENVIRONMENT_WAREHOUSE_PREFIX}{client_api_key}"
    _get_client().delete(redis_key)


def pop_warehouse_delivery_statuses() -> list[WarehouseDeliveryStatus]:
    """Takes every outcome the warehouse-delivery service has left in Redis,
    emptying the hash as it goes. An entry that cannot be read is logged and
    skipped rather than blocking the others."""
    # The stub types eval for the async client too; this client is synchronous
    # and a Lua HGETALL comes back as a flat field, value, field, value list.
    entries = cast(
        list[bytes],
        _get_client().eval(_POP_HASH_SCRIPT, 1, WAREHOUSE_DELIVERY_STATUS_KEY),
    )
    statuses: list[WarehouseDeliveryStatus] = []
    for field, value in zip(entries[::2], entries[1::2], strict=True):
        try:
            outcome = json.loads(value)
            detail = outcome.get("detail")
            status = WarehouseDeliveryStatus(
                connection_id=int(field),
                status=str(outcome["status"]),
                detail=str(detail) if detail is not None else None,
            )
        except (ValueError, KeyError, TypeError, AttributeError):
            logger.warning(
                "delivery_status.unreadable",
                field=field.decode(errors="replace"),
                exc_info=True,
            )
            continue
        statuses.append(status)
    return statuses
