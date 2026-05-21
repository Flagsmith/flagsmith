from typing import Any

from rest_framework import serializers

from environments.models import Environment
from experimentation.models import (
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseType,
)
from experimentation.types import SNOWFLAKE_DEFAULTS, SnowflakeConfig


class WarehouseConnectionSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    name = serializers.CharField(max_length=255, required=False)
    config = serializers.JSONField(default=None, required=False, allow_null=True)

    class Meta:
        model = WarehouseConnection
        fields = ("id", "warehouse_type", "status", "name", "config", "created_at")
        read_only_fields = ("id", "status", "created_at")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        warehouse_type: str = attrs.get(
            "warehouse_type",
            getattr(self.instance, "warehouse_type", ""),
        )
        config: dict[str, Any] | None = attrs.get("config")

        if warehouse_type == WarehouseType.SNOWFLAKE:
            attrs["config"] = self._validate_snowflake_config(config or {})
        elif warehouse_type == WarehouseType.FLAGSMITH:
            if config:
                raise serializers.ValidationError(
                    {"config": "Flagsmith warehouse does not accept configuration."}
                )
            attrs["config"] = None
        return attrs

    def create(
        self,
        validated_data: dict[str, Any],
    ) -> WarehouseConnection:
        environment: Environment = validated_data["environment"]
        warehouse_type: str = validated_data["warehouse_type"]

        if not validated_data.get("name"):
            validated_data["name"] = self._generate_name(warehouse_type, environment)

        existing: WarehouseConnection | None = (
            WarehouseConnection.objects.all_with_deleted()
            .filter(
                environment=environment,
                warehouse_type=warehouse_type,
                deleted_at__isnull=False,
            )
            .first()
        )
        if existing:
            existing.deleted_at = None
            existing.status = WarehouseConnectionStatus.CREATED
            existing.name = validated_data["name"]
            existing.config = validated_data.get("config")
            existing.save()
            return existing

        result: WarehouseConnection = super().create(validated_data)
        return result

    @staticmethod
    def _generate_name(warehouse_type: str, environment: Environment) -> str:
        label = WarehouseType(warehouse_type).label
        return f"{label} Warehouse - {environment.name}"

    @staticmethod
    def _validate_snowflake_config(config: dict[str, Any]) -> SnowflakeConfig:
        account_identifier = config.get("account_identifier", "")
        if not account_identifier:
            raise serializers.ValidationError(
                {"config": {"account_identifier": "This field is required."}}
            )
        merged: SnowflakeConfig = {
            **SNOWFLAKE_DEFAULTS,
            **config,  # type: ignore[typeddict-item]
        }
        return merged
