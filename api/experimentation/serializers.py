from typing import Any

from rest_framework import serializers

from environments.models import Environment
from experimentation.metric_definitions import validate_metric_definition
from experimentation.models import (
    Experiment,
    ExperimentMetric,
    ExperimentStatus,
    Metric,
    WarehouseConnection,
    WarehouseType,
)
from experimentation.types import SNOWFLAKE_DEFAULTS, SnowflakeConfig
from features.feature_types import MULTIVARIATE
from features.models import Feature
from features.multivariate.serializers import NestedMultivariateFeatureOptionSerializer


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


class MetricSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    class Meta:
        model = Metric
        fields = (
            "id",
            "name",
            "description",
            "aggregation",
            "direction",
            "definition",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        error = validate_metric_definition(attrs["definition"])
        if error:
            raise serializers.ValidationError({"definition": error})
        return attrs


class ExperimentMetricSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    metric = serializers.PrimaryKeyRelatedField(  # type: ignore[var-annotated]
        queryset=Metric.objects.all(),
    )
    metric_name = serializers.CharField(source="metric.name", read_only=True)
    aggregation = serializers.CharField(source="metric.aggregation", read_only=True)

    class Meta:
        model = ExperimentMetric
        fields = (
            "id",
            "metric",
            "metric_name",
            "aggregation",
            "expected_direction",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        experiment: Experiment = self.context["experiment"]

        if experiment.status == ExperimentStatus.COMPLETED:
            raise serializers.ValidationError(
                "Cannot modify metrics of a completed experiment."
            )

        metric: Metric = attrs.get("metric", getattr(self.instance, "metric", None))

        if metric.environment_id != experiment.environment_id:
            raise serializers.ValidationError(
                {"metric": "Metric must belong to the experiment's environment."}
            )

        attached = experiment.experiment_metrics.all()
        if isinstance(self.instance, ExperimentMetric):
            attached = attached.exclude(pk=self.instance.pk)

        if "metric" in attrs and attached.filter(metric=metric).exists():
            raise serializers.ValidationError(
                {"metric": "Metric is already attached to this experiment."}
            )
        return attrs


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
            "status",
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
        environment: Environment | None = self.context.get("environment")
        if environment and feature.project_id != environment.project_id:
            raise serializers.ValidationError(
                "Feature does not belong to this environment's project."
            )
        return feature

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if self.instance is not None and "feature" in attrs:
            raise serializers.ValidationError(
                {"feature": "Cannot change the feature of an existing experiment."}
            )
        return attrs


class ExperimentFeatureSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    multivariate_options = NestedMultivariateFeatureOptionSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = Feature
        fields = ("id", "name", "type", "initial_value", "multivariate_options")
        read_only_fields = fields


class ExperimentListSerializer(ExperimentSerializer):
    feature = ExperimentFeatureSerializer(read_only=True)
