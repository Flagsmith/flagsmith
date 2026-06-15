import typing
from dataclasses import asdict
from datetime import datetime

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_CREATE,
    AFTER_DELETE,
    LifecycleModelMixin,
    hook,
)

from core.models import SoftDeleteExportableModel
from environments.models import Environment
from experimentation.types import MetricDefinition

if typing.TYPE_CHECKING:
    from experimentation.dataclasses import ExposuresSummary, WarehouseEventStats


class WarehouseType(models.TextChoices):
    FLAGSMITH = "flagsmith", "Flagsmith"
    SNOWFLAKE = "snowflake", "Snowflake"
    CLICKHOUSE = "clickhouse", "ClickHouse"


class WarehouseConnectionStatus(models.TextChoices):
    CREATED = "created", "Created"
    PENDING_CONNECTION = "pending_connection", "Pending Connection"
    CONNECTED = "connected", "Connected"
    ERRORED = "errored", "Errored"


class WarehouseConnection(LifecycleModelMixin, SoftDeleteExportableModel):  # type: ignore[misc]
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name="warehouse_connections",
    )
    warehouse_type = models.CharField(
        max_length=50,
        choices=WarehouseType.choices,
    )
    status = models.CharField(
        max_length=50,
        choices=WarehouseConnectionStatus.choices,
        default=WarehouseConnectionStatus.CREATED,
    )
    name = models.CharField(max_length=255)
    config: models.JSONField[dict[str, object] | None, dict[str, object] | None] = (
        models.JSONField(null=True, blank=True)
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Populated at serialization time for flagsmith connections from ClickHouse;
    # never persisted to the database.
    event_stats: "WarehouseEventStats | None" = None

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_warehouse_per_env",
            ),
        ]

    @hook(AFTER_CREATE)  # type: ignore[misc]
    def sync_to_ingestion_on_create(self) -> None:
        from experimentation.tasks import add_environment_key_to_ingestion

        add_environment_key_to_ingestion.delay(
            kwargs={"environment_api_key": self.environment.api_key},
        )

    @hook(AFTER_DELETE)  # type: ignore[misc]
    def sync_to_ingestion_on_delete(self) -> None:
        from experimentation.tasks import delete_environment_key_from_ingestion

        delete_environment_key_from_ingestion.delay(
            kwargs={"environment_api_key": self.environment.api_key},
        )


class ExperimentStatus(models.TextChoices):
    CREATED = "created", "Created"
    RUNNING = "running", "Running"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"


VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    ExperimentStatus.CREATED: {ExperimentStatus.RUNNING},
    ExperimentStatus.RUNNING: {ExperimentStatus.PAUSED, ExperimentStatus.COMPLETED},
    ExperimentStatus.PAUSED: {ExperimentStatus.RUNNING, ExperimentStatus.COMPLETED},
    ExperimentStatus.COMPLETED: set(),
}


class Experiment(LifecycleModelMixin, SoftDeleteExportableModel):  # type: ignore[misc]
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name="experiments",
    )
    feature = models.ForeignKey(
        "features.Feature",
        on_delete=models.CASCADE,
        related_name="experiments",
    )
    name = models.CharField(max_length=255)
    hypothesis = models.TextField()
    status = models.CharField(
        max_length=50,
        choices=ExperimentStatus.choices,
        default=ExperimentStatus.CREATED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["feature", "environment"],
                condition=Q(deleted_at__isnull=True) & ~Q(status="completed"),
                name="unique_active_experiment_per_feature_env",
            ),
        ]


class ExperimentExposures(models.Model):
    experiment = models.OneToOneField(
        Experiment,
        on_delete=models.CASCADE,
        related_name="exposures",
    )
    as_of = models.DateTimeField(null=True, blank=True)
    payload: models.JSONField[dict[str, object] | None, dict[str, object] | None] = (
        models.JSONField(null=True, blank=True)
    )
    last_error_at = models.DateTimeField(null=True, blank=True)
    refresh_requested_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_final(self) -> bool:
        ended_at = self.experiment.ended_at
        return (
            ended_at is not None and self.as_of is not None and self.as_of >= ended_at
        )

    def record_refresh(self, summary: "ExposuresSummary", as_of: datetime) -> None:
        self.payload = asdict(summary)
        self.as_of = as_of
        self.last_error_at = None
        self.save(update_fields=["payload", "as_of", "last_error_at"])

    def record_failure(self) -> None:
        self.last_error_at = timezone.now()
        self.save(update_fields=["last_error_at"])

    def record_refresh_request(self) -> None:
        self.refresh_requested_at = timezone.now()
        self.save(update_fields=["refresh_requested_at"])


class MetricAggregation(models.TextChoices):
    COUNT = "count", "Count"
    SUM = "sum", "Sum"
    MEAN = "mean", "Mean"
    OCCURRENCE = "occurrence", "Occurrence (event happened at least once)"


class MetricDirection(models.TextChoices):
    """A metric's inherent polarity — which way is "better"."""

    UP = "up", "Higher is better"
    DOWN = "down", "Lower is better"
    INFORMATIONAL = "informational", "Informational only"


class ExpectedDirection(models.TextChoices):
    """The guardrail direction expected of a metric within an experiment."""

    INCREASE = "increase", "Increase"
    DECREASE = "decrease", "Decrease"
    NOT_INCREASE = "not_increase", "Should not increase"
    NOT_DECREASE = "not_decrease", "Should not decrease"


class Metric(SoftDeleteExportableModel):
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    aggregation = models.CharField(
        max_length=20,
        choices=MetricAggregation.choices,
        default=MetricAggregation.MEAN,
    )
    direction = models.CharField(
        max_length=20,
        choices=MetricDirection.choices,
        default=MetricDirection.UP,
    )
    definition: models.JSONField[MetricDefinition, MetricDefinition] = (
        models.JSONField()
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ExperimentMetric(models.Model):
    experiment = models.ForeignKey(
        Experiment,
        on_delete=models.CASCADE,
        related_name="experiment_metrics",
    )
    metric = models.ForeignKey(
        Metric,
        on_delete=models.CASCADE,
        related_name="experiment_metrics",
    )
    expected_direction = models.CharField(
        max_length=20,
        choices=ExpectedDirection.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["experiment", "metric"],
                name="metric_attached_once_per_experiment",
            ),
        ]
