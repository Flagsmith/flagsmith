from typing import Any

from rest_framework import serializers

from experimentation.models import WarehouseConnection
from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation
from experimentation.warehouses.registry import get_warehouse


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
                {"credentials": "Only ClickHouse connections accept credentials."}
            )
        if instance is not None and instance.credentials is not None:
            attrs["credentials"] = None
