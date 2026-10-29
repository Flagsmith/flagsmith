import hashlib
import json
import typing

from django.core.cache import cache

from experimentation.dataclasses import WarehouseEventNames, WarehouseEventStats

if typing.TYPE_CHECKING:
    from experimentation.models import WarehouseConnection

CUSTOMER_EVENT_UNAVAILABLE = "unavailable"


def customer_cache_key(kind: str, connection: "WarehouseConnection") -> str:
    """Key cached warehouse reads by the connection's non-secret details, so a
    config or type change can neither serve nor store stale reads. Credentials
    stay out of the key material: they don't determine what the warehouse
    holds, so rotating them keeps the cache valid."""
    details = json.dumps(
        [connection.warehouse_type, connection.config],
        sort_keys=True,
    )
    digest = hashlib.sha256(details.encode()).hexdigest()[:12]
    return f"experimentation:customer_{kind}:{connection.id}:{digest}"


def cache_warehouse_read_unless_empty(
    cache_key: str,
    result: WarehouseEventNames | WarehouseEventStats,
    seconds: int,
) -> None:
    """A read before the first event lands must not pin "no events" for the TTL."""
    if isinstance(result, WarehouseEventNames):
        is_empty = not result.events
    else:
        is_empty = not result.total_events_received
    if not is_empty:
        cache.set(cache_key, result, seconds)
