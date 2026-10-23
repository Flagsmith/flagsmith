import hashlib
import json
import typing

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
