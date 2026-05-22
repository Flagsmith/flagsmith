from django.db import models
from django_lifecycle import LifecycleModelMixin  # type: ignore[import-untyped]

from core.models import SoftDeleteExportableModel
from environments.models import Environment


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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse_type", "environment"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_warehouse_per_type_and_env",
            ),
        ]
