from django.db import models
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_CREATE,
    AFTER_DELETE,
    LifecycleModelMixin,
    hook,
)

from core.models import SoftDeleteExportableModel
from environments.models import Environment
from experimentation.tasks import (
    add_environment_key_to_ingestion,
    delete_environment_key_from_ingestion,
)


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
                fields=["environment"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_warehouse_per_env",
            ),
        ]

    @hook(AFTER_CREATE)  # type: ignore[misc]
    def sync_to_ingestion_on_create(self) -> None:
        add_environment_key_to_ingestion.delay(
            kwargs={"environment_api_key": self.environment.api_key},
        )

    @hook(AFTER_DELETE)  # type: ignore[misc]
    def sync_to_ingestion_on_delete(self) -> None:
        delete_environment_key_from_ingestion.delay(
            kwargs={"environment_api_key": self.environment.api_key},
        )
