import json
from collections.abc import Iterable, Sequence
from typing import cast

import structlog
from django.conf import settings
from redis.exceptions import RedisError

from experimentation.dataclasses import WarehouseDeliveryStatus
from experimentation.ingestion_redis import get_client
from experimentation.warehouse_credentials import encrypt_warehouse_credentials

# Read by the warehouse-delivery service to find the warehouse an environment's
# events go to. The rest of the key is the environment's client API key, the
# same value the ingestion server puts on each Kafka message.
WAREHOUSE_CONNECTION_KEY_PREFIX = "experimentation:environment_warehouses:"
# One hash the warehouse-delivery service writes each connection's latest
# outcome into, under the connection id, overwriting the previous one.
WAREHOUSE_DELIVERY_STATUS_KEY = "experimentation:warehouse_delivery_status"

logger = structlog.get_logger("experimentation")


def publish_warehouse_connection(
    client_api_key: str,
    *,
    connection_id: int,
    warehouse_type: str,
    config: dict[str, object],
    credentials: dict[str, object] | None,
) -> None:
    """Tells the warehouse-delivery service which warehouse the environment's
    events go to. Credentials travel as the same Fernet ciphertext the database
    holds, so only a service that has WAREHOUSE_CREDENTIALS_SECRET can read
    them out of Redis."""
    redis_key = f"{WAREHOUSE_CONNECTION_KEY_PREFIX}{client_api_key}"
    document = {
        "connection_id": connection_id,
        "warehouse_type": warehouse_type,
        "config": config,
        "credentials": (
            encrypt_warehouse_credentials(credentials)
            if credentials is not None
            else None
        ),
    }
    get_client().set(redis_key, json.dumps(document))


def remove_warehouse_connection(
    client_api_key: str,
    *,
    connection_ids: Iterable[int],
) -> None:
    """Stops the warehouse-delivery service delivering for the environment and
    forgets the outcomes it left for these connections, so a connection that
    is deleted or switched back to Flagsmith's warehouse never shows a stale
    failure."""
    redis_key = f"{WAREHOUSE_CONNECTION_KEY_PREFIX}{client_api_key}"
    client = get_client()
    client.delete(redis_key)
    fields = [str(connection_id) for connection_id in connection_ids]
    if fields:
        client.hdel(WAREHOUSE_DELIVERY_STATUS_KEY, *fields)


def get_warehouse_delivery_statuses(
    connection_ids: Sequence[int],
) -> dict[int, WarehouseDeliveryStatus]:
    """The latest outcome the warehouse-delivery service left for each of these
    connections, by id. A connection it has never delivered for is absent.

    Returns nothing at all when the ingestion Redis is not configured or does
    not answer, so the connections page never depends on it being up."""
    if not connection_ids or not settings.INGESTION_REDIS_URL:
        return {}
    fields = [str(connection_id) for connection_id in connection_ids]
    try:
        # The stub types hmget for the async client too; this client is
        # synchronous.
        values = cast(
            list[bytes | None],
            get_client().hmget(WAREHOUSE_DELIVERY_STATUS_KEY, fields),
        )
    except RedisError:
        logger.warning("delivery_status.unavailable", exc_info=True)
        return {}
    statuses: dict[int, WarehouseDeliveryStatus] = {}
    for connection_id, value in zip(connection_ids, values, strict=True):
        if value is None:
            continue
        try:
            outcome = json.loads(value)
            detail = outcome.get("detail")
            statuses[connection_id] = WarehouseDeliveryStatus(
                connection_id=connection_id,
                status=str(outcome["status"]),
                detail=str(detail) if detail is not None else None,
            )
        except (ValueError, KeyError, TypeError, AttributeError):
            logger.warning(
                "delivery_status.unreadable",
                connection__id=connection_id,
                exc_info=True,
            )
    return statuses
