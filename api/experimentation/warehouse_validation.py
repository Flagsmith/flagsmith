from typing import Any

from rest_framework import serializers

from environments.models import Environment
from experimentation.models import WarehouseConnection, WarehouseType
from experimentation.services import is_warehouse_type_available
from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation
from experimentation.warehouses.postgres import is_flagsmith_database_config
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
    config = attrs.get("config", getattr(instance, "config", None))
    # Any `source` selects the mode, so validate_config reports a malformed marker.
    if (
        warehouse_type == WarehouseType.POSTGRES
        and isinstance(config, dict)
        and "source" in config
    ):
        if attrs.get("credentials") is not None:
            raise serializers.ValidationError(
                {"credentials": "The Flagsmith database takes no credentials."}
            )
        if instance is not None and instance.credentials is not None:
            attrs["credentials"] = None
        return
    if (
        "credentials" not in attrs
        and instance is not None
        and instance.warehouse_type == warehouse_type
        and not is_flagsmith_database_config(instance.config)
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
