from typing import Any

from django.db import transaction
from django.db.models import QuerySet
from rest_framework import serializers

from core.dataclasses import AuthorData
from environments.models import Environment
from experimentation.dataclasses import RolloutSpec, WarehouseEventStats
from experimentation.metric_definitions import validate_metric_definition
from experimentation.models import (
    ExpectedDirection,
    Experiment,
    ExperimentExposures,
    ExperimentMetric,
    ExperimentResults,
    ExperimentStatus,
    Metric,
    WarehouseConnection,
    WarehouseType,
)
from experimentation.services import (
    apply_experiment_rollout,
    get_experiment_rollout,
)
from experimentation.types import (
    SNOWFLAKE_DEFAULTS,
    MetricExperimentResult,
    SnowflakeConfig,
)
from features.feature_states.serializers import (
    FeatureValueSerializer,
    MultivariateValueSerializer,
)
from features.feature_types import MULTIVARIATE
from features.models import Feature
from features.multivariate.serializers import NestedMultivariateFeatureOptionSerializer
from features.versioning.dataclasses import MultivariateValueChangeSet


class WarehouseConnectionSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    name = serializers.CharField(max_length=255, required=False)
    config = serializers.JSONField(default=None, required=False, allow_null=True)
    total_events_received = serializers.SerializerMethodField()
    unique_events_count = serializers.SerializerMethodField()

    class Meta:
        model = WarehouseConnection
        fields = (
            "id",
            "warehouse_type",
            "status",
            "name",
            "config",
            "created_at",
            "total_events_received",
            "unique_events_count",
        )
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

    def get_total_events_received(self, obj: WarehouseConnection) -> int | None:
        stats: WarehouseEventStats | None = obj.event_stats
        return stats.total_events_received if stats else None

    def get_unique_events_count(self, obj: WarehouseConnection) -> int | None:
        stats: WarehouseEventStats | None = obj.event_stats
        return stats.unique_events_count if stats else None

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
    experiments = serializers.SerializerMethodField()

    class Meta:
        model = Metric
        fields = (
            "id",
            "name",
            "description",
            "aggregation",
            "direction",
            "definition",
            "experiments",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "experiments",
            "created_at",
            "updated_at",
        )

    def get_experiments(self, metric: Metric) -> list[MetricExperimentResult]:
        return [
            {
                "id": experiment_metric.experiment.id,
                "name": experiment_metric.experiment.name,
                "status": experiment_metric.experiment.status,
            }
            for experiment_metric in metric.experiment_metrics.all()
        ]

    def validate_definition(self, definition: object) -> object:
        error = validate_metric_definition(definition)
        if error:
            raise serializers.ValidationError(error)
        return definition


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


class _EnvironmentScopedMetricField(serializers.PrimaryKeyRelatedField[Metric]):
    def get_queryset(self) -> QuerySet[Metric]:
        queryset: QuerySet[Metric] = Metric.objects.filter(
            environment=self.context["environment"]
        )
        return queryset


class ExperimentMetricInlineSerializer(serializers.Serializer):  # type: ignore[type-arg]
    metric = _EnvironmentScopedMetricField()
    expected_direction = serializers.ChoiceField(choices=ExpectedDirection.choices)


class ExperimentRolloutSerializer(serializers.Serializer):  # type: ignore[type-arg]
    enabled = serializers.BooleanField(required=True)
    rollout_percentage = serializers.FloatField(
        required=True, min_value=0, max_value=100
    )
    feature_state_value = FeatureValueSerializer(required=True)
    multivariate_feature_state_values = MultivariateValueSerializer(
        many=True, required=False
    )

    @staticmethod
    def to_spec(data: dict[str, Any], request: Any) -> RolloutSpec:
        value = data["feature_state_value"]
        return RolloutSpec(
            enabled=data["enabled"],
            rollout_percentage=data["rollout_percentage"],
            feature_state_value=value["value"],
            value_type=value["type"],
            multivariate_values=[
                MultivariateValueChangeSet(
                    multivariate_feature_option_id=mv["multivariate_feature_option"],
                    percentage_allocation=mv["percentage_allocation"],
                )
                for mv in data.get("multivariate_feature_state_values", [])
            ],
            author=AuthorData.from_request(request),
        )


class ExperimentSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    # Annotated with the common base type so ExperimentListSerializer can
    # override the field with a read-only representation.
    metrics: serializers.BaseSerializer[Any] = ExperimentMetricInlineSerializer(
        many=True,
        required=False,
        write_only=True,
    )
    experiment_rollout: Any = ExperimentRolloutSerializer(
        required=False, write_only=True
    )

    class Meta:
        model = Experiment
        fields = (
            "id",
            "feature",
            "name",
            "hypothesis",
            "status",
            "metrics",
            "experiment_rollout",
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
        if self.instance is not None and "metrics" in attrs:
            raise serializers.ValidationError(
                {"metrics": "Cannot change the metrics of an existing experiment."}
            )
        if self.instance is not None and "experiment_rollout" in attrs:
            raise serializers.ValidationError(
                {
                    "experiment_rollout": (
                        "Cannot change the rollout via this endpoint; "
                        "use the rollout endpoint instead."
                    )
                }
            )
        self._validate_metrics(attrs.get("metrics") or [])
        return attrs

    def _validate_metrics(self, metrics: list[dict[str, Any]]) -> None:
        metric_ids = [entry["metric"].id for entry in metrics]
        if len(metric_ids) != len(set(metric_ids)):
            raise serializers.ValidationError(
                {"metrics": "Metric can only be attached once per experiment."}
            )

    def create(self, validated_data: dict[str, Any]) -> Experiment:
        metrics: list[dict[str, Any]] = validated_data.pop("metrics", [])
        rollout: dict[str, Any] | None = validated_data.pop("experiment_rollout", None)
        with transaction.atomic():
            experiment: Experiment = super().create(validated_data)
            ExperimentMetric.objects.bulk_create(
                ExperimentMetric(
                    experiment=experiment,
                    metric=entry["metric"],
                    expected_direction=entry["expected_direction"],
                )
                for entry in metrics
            )
            if rollout is not None:
                apply_experiment_rollout(
                    experiment,
                    ExperimentRolloutSerializer.to_spec(
                        rollout, self.context["request"]
                    ),
                )
        return experiment


class ExperimentFeatureSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    multivariate_options = serializers.SerializerMethodField()

    class Meta:
        model = Feature
        fields = ("id", "name", "type", "initial_value", "multivariate_options")
        read_only_fields = fields

    def get_multivariate_options(self, feature: Feature) -> list[dict[str, Any]]:
        options = NestedMultivariateFeatureOptionSerializer(
            feature.multivariate_options.all(), many=True
        ).data

        environment: Environment | None = self.context.get("environment")
        if not environment:
            raise ValueError(
                "ExperimentFeatureSerializer requires 'environment' in context."
            )

        env_state = (
            feature.feature_states.filter(
                environment=environment,
                identity__isnull=True,
                feature_segment__isnull=True,
            )
            .order_by("-live_from", "-version")
            .first()
        )
        if not env_state:
            raise ValueError(
                f"No environment feature state found for feature {feature.id} "
                f"in environment {environment.id}."
            )

        alloc_map = dict(
            env_state.multivariate_feature_state_values.values_list(
                "multivariate_feature_option_id", "percentage_allocation"
            )
        )
        for option in options:
            if option["id"] in alloc_map:
                option["default_percentage_allocation"] = alloc_map[option["id"]]

        return options  # type: ignore[return-value]


class ExperimentListSerializer(ExperimentSerializer):
    feature = ExperimentFeatureSerializer(read_only=True)
    metrics = ExperimentMetricSerializer(
        source="experiment_metrics",
        many=True,
        read_only=True,
    )


class ExperimentDetailSerializer(ExperimentListSerializer):
    experiment_rollout = serializers.SerializerMethodField()

    def get_experiment_rollout(self, experiment: Experiment) -> dict[str, Any] | None:
        return get_experiment_rollout(experiment)


class ExperimentExposuresSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    is_final = serializers.BooleanField(read_only=True)

    class Meta:
        model = ExperimentExposures
        fields = (
            "as_of",
            "last_error_at",
            "refresh_requested_at",
            "payload",
            "is_final",
        )


class ExperimentResultsSerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    is_final = serializers.BooleanField(read_only=True)

    class Meta:
        model = ExperimentResults
        fields = (
            "as_of",
            "last_error_at",
            "refresh_requested_at",
            "payload",
            "is_final",
        )
