from typing import Any

from rest_framework import serializers

from environments.models import Environment
from experimentation.models import WarehouseConnection, WarehouseType
from experimentation.services import is_warehouse_type_available
from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation
from experimentation.warehouses.registry import get_warehouse


def validate_warehouse_type_allowed(
    warehouse_type: str,
    instance: WarehouseConnection | None,
    environment: Environment | None,
) -> None:
    if instance is not None and instance.warehouse_type == warehouse_type:
        return
    if environment is None or is_warehouse_type_available(
        environment.project.organisation, warehouse_type
    ):
        return
    raise serializers.ValidationError(
        {
            "warehouse_type": f"{WarehouseType(warehouse_type).label} connections "
            "are not available on your plan."
        }
    )


def validate_credentials(
    attrs: dict[str, Any],
    warehouse_type: str,
    instance: WarehouseConnection | None,
) -> None:
    if (
        "credentials" not in attrs
        and instance is not None
        and instance.warehouse_type == warehouse_type
    ):
        return
    credentials: dict[str, Any] | None = attrs.get("credentials")
    try:
        attrs["credentials"] = get_warehouse(warehouse_type).validate_credentials(
            credentials or {}
        )
    except UnsupportedWarehouseOperation:
        if credentials is not None:
            raise serializers.ValidationError(
                {"credentials": "This warehouse type does not accept credentials."}
            )
        if instance is not None and instance.credentials is not None:
            attrs["credentials"] = None


# Their stored password would otherwise follow a host change to the new host.
HOST_BOUND_CREDENTIAL_TYPES = frozenset({WarehouseType.POSTGRES})


def validate_host_change_resends_credentials(
    attrs: dict[str, Any],
    warehouse_type: str,
    instance: WarehouseConnection | None,
) -> None:
    if (
        warehouse_type not in HOST_BOUND_CREDENTIAL_TYPES
        or instance is None
        or instance.warehouse_type != warehouse_type
        or "credentials" in attrs
    ):
        return
    stored_host = (instance.config or {}).get("host")
    if (attrs.get("config") or {}).get("host") != stored_host:
        raise serializers.ValidationError(
            {"config": {"host": "Re-enter the password when changing the host."}}
        )
