from typing import Any

from rest_framework import serializers

from environments.models import Environment
from experimentation.models import WarehouseConnection, WarehouseType
from experimentation.services import is_databricks_warehouse_enabled
from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation
from experimentation.warehouses.registry import get_warehouse


def validate_warehouse_type_allowed(
    warehouse_type: str,
    instance: WarehouseConnection | None,
    environment: Environment | None,
) -> None:
    if warehouse_type != WarehouseType.DATABRICKS:
        return
    if instance is not None and instance.warehouse_type == warehouse_type:
        return
    if environment is None or not is_databricks_warehouse_enabled(
        environment.project.organisation
    ):
        raise serializers.ValidationError(
            {"warehouse_type": "Databricks connections are not available yet."}
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
