import json
from collections.abc import Iterable

from experimentation.ingestion_redis import get_client
from experimentation.warehouse_credentials import encrypt_warehouse_credentials

# Read by the warehouse-delivery service to find the warehouse an environment's
# events go to. The rest of the key is the environment's client API key, the
# same value the ingestion server puts on each Kafka message.
WAREHOUSE_CONNECTION_KEY_PREFIX = "experimentation:environment_warehouses:"
# One hash the warehouse-delivery service writes each connection's latest
# outcome into, under the connection id, overwriting the previous one.
WAREHOUSE_DELIVERY_STATUS_KEY = "experimentation:warehouse_delivery_status"


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


def remove_warehouse_connection(client_api_key: str) -> None:
    get_client().delete(f"{WAREHOUSE_CONNECTION_KEY_PREFIX}{client_api_key}")


def delete_warehouse_delivery_statuses(connection_ids: Iterable[int]) -> None:
    fields = [str(connection_id) for connection_id in connection_ids]
    if fields:
        get_client().hdel(WAREHOUSE_DELIVERY_STATUS_KEY, *fields)
