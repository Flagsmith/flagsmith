from typing import Any

from rest_framework import serializers

from environments.models import Environment
from experimentation.models import (
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseType,
)


class WarehouseConnectionSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = WarehouseConnection
        fields = ("id", "warehouse_type", "status", "name", "created_at")
        read_only_fields = ("id", "status", "name", "created_at")

    def create(
        self,
        validated_data: dict[str, Any],
    ) -> WarehouseConnection:
        environment: Environment = validated_data["environment"]
        warehouse_type: str = validated_data["warehouse_type"]

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
            existing.status = WarehouseConnectionStatus.PENDING_CONNECTION
            existing.name = self._generate_name(warehouse_type, environment)
            existing.save()
            return existing

        validated_data["name"] = self._generate_name(warehouse_type, environment)
        result: WarehouseConnection = super().create(validated_data)
        return result

    @staticmethod
    def _generate_name(warehouse_type: str, environment: Environment) -> str:
        label = WarehouseType(warehouse_type).label
        return f"{label} Warehouse - {environment.name}"
