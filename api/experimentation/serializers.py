from typing import Any

from django.utils import timezone
from rest_framework import serializers

from environments.models import Environment
from experimentation.models import (
    VALID_STATUS_TRANSITIONS,
    Experiment,
    ExperimentStatus,
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseType,
)
from experimentation.types import SNOWFLAKE_DEFAULTS, SnowflakeConfig
from features.feature_types import MULTIVARIATE


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

        if "config" not in attrs and self.instance is not None:
            return attrs

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


class ExperimentSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Experiment
        fields = (
            "id",
            "feature",
            "name",
            "hypothesis",
            "status",
            "created_at",
            "updated_at",
            "started_at",
            "ended_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "started_at",
            "ended_at",
        )

    def validate_feature(self, feature: Any) -> Any:
        if feature.type != MULTIVARIATE:
            raise serializers.ValidationError(
                "Experiments can only be created for multivariate flags."
            )
        view = self.context.get("view")
        if view:
            environment: Environment = view._get_environment()
            if feature.project_id != environment.project_id:
                raise serializers.ValidationError(
                    "Feature does not belong to this environment's project."
                )
        return feature

    def validate_status(self, status: str) -> str:
        if self.instance is None:
            if status != ExperimentStatus.CREATED:
                raise serializers.ValidationError(
                    "Status must be 'created' when creating an experiment."
                )
            return status

        current_status: str = self.instance.status  # type: ignore[union-attr]
        if status == current_status:
            return status

        valid_targets = VALID_STATUS_TRANSITIONS.get(current_status, set())
        if status not in valid_targets:
            raise serializers.ValidationError(
                f"Cannot transition from '{current_status}' to '{status}'."
            )
        return status

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if self.instance is not None and "feature" in attrs:
            raise serializers.ValidationError(
                {"feature": "Cannot change the feature of an existing experiment."}
            )
        return attrs

    def update(
        self,
        instance: Experiment,
        validated_data: dict[str, Any],
    ) -> Experiment:
        new_status = validated_data.get("status")
        if new_status == ExperimentStatus.RUNNING and instance.started_at is None:
            validated_data["started_at"] = timezone.now()
        elif new_status == ExperimentStatus.COMPLETED:
            validated_data["ended_at"] = timezone.now()
        result: Experiment = super().update(instance, validated_data)
        return result
