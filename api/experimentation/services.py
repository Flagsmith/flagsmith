from __future__ import annotations

import typing
from functools import lru_cache

import structlog
from clickhouse_driver import Client
from django.conf import settings
from django.utils import timezone

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from experimentation.constants import EXPERIMENT_FLAG, WAREHOUSE_CONNECTION_FLAG
from experimentation.dataclasses import WarehouseEventStats
from experimentation.models import (
    VALID_STATUS_TRANSITIONS,
    ExperimentStatus,
    WarehouseConnectionStatus,
    WarehouseType,
)
from integrations.flagsmith.client import get_openfeature_client

if typing.TYPE_CHECKING:
    from experimentation.models import Experiment, WarehouseConnection
    from organisations.models import Organisation
    from users.models import FFAdminUser

logger = structlog.get_logger("warehouse")


def is_warehouse_feature_enabled(organisation: Organisation) -> bool:
    return get_openfeature_client().get_boolean_value(
        WAREHOUSE_CONNECTION_FLAG,
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )


def is_experiment_feature_enabled(organisation: Organisation) -> bool:
    return get_openfeature_client().get_boolean_value(
        EXPERIMENT_FLAG,
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )


@lru_cache(maxsize=1)
def _get_clickhouse_client() -> Client:
    """Build a clickhouse-driver client for the experimentation event store.

    The database is taken from the DSN path, so queries can reference the
    `events` table unqualified.
    """
    return Client.from_url(settings.EXPERIMENTATION_CLICKHOUSE_URL)


def get_unique_event_names(environment_key: str) -> list[str]:
    """Return the distinct event names recorded for `environment_key`,
    ordered alphabetically."""
    rows = _get_clickhouse_client().execute(
        "SELECT DISTINCT event FROM events "
        "WHERE environment_key = %(environment_key)s "
        "ORDER BY event",
        {"environment_key": environment_key},
    )
    return [row[0] for row in rows]


def get_warehouse_event_stats(environment_key: str) -> WarehouseEventStats:
    """Return event counts recorded for `environment_key` in the warehouse."""
    rows = _get_clickhouse_client().execute(
        "SELECT count() AS total, uniqExact(event) AS unique "
        "FROM events WHERE environment_key = %(environment_key)s",
        {"environment_key": environment_key},
    )
    total, unique = rows[0] if rows else (0, 0)
    return WarehouseEventStats(
        total_events_received=int(total),
        unique_events_count=int(unique),
    )


def _resolve_audit_log_author(
    user: FFAdminUser,
) -> dict[str, int | None]:
    if getattr(user, "is_master_api_key_user", False):
        return {"author_id": None, "master_api_key_id": user.key.id}
    return {"author_id": user.pk, "master_api_key_id": None}


def create_warehouse_audit_log(
    connection: WarehouseConnection,
    user: FFAdminUser,
    *,
    action: str,
) -> None:
    AuditLog.objects.create(
        environment=connection.environment,
        project=connection.environment.project,
        **_resolve_audit_log_author(user),
        related_object_id=connection.id,
        related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        log=(
            f"Warehouse connection {action} for environment "
            f"{connection.environment.name}"
        ),
    )


def create_experiment_audit_log(
    experiment: Experiment,
    user: FFAdminUser,
    *,
    action: str,
) -> None:
    AuditLog.objects.create(
        environment=experiment.environment,
        project=experiment.environment.project,
        **_resolve_audit_log_author(user),
        related_object_id=experiment.id,
        related_object_type=RelatedObjectType.EXPERIMENT.name,
        log=(
            f"Experiment '{experiment.name}' {action} for environment "
            f"{experiment.environment.name}"
        ),
    )


def transition_experiment_status(
    experiment: Experiment,
    target_status: str,
    user: FFAdminUser,
) -> Experiment:
    valid_targets = VALID_STATUS_TRANSITIONS.get(experiment.status, set())
    if target_status not in valid_targets:
        raise ValueError(
            f"Cannot transition from '{experiment.status}' to '{target_status}'."
        )

    experiment.status = target_status

    if target_status == ExperimentStatus.RUNNING and not experiment.started_at:
        experiment.started_at = timezone.now()
    elif target_status == ExperimentStatus.COMPLETED:
        experiment.ended_at = timezone.now()

    experiment.save()
    create_experiment_audit_log(experiment, user, action=target_status)
    return experiment


def mark_warehouse_pending_connection(
    connection: WarehouseConnection,
) -> WarehouseConnection:
    """Move a connection from created to pending_connection. No-op for any
    other status."""
    if connection.status != WarehouseConnectionStatus.CREATED:
        return connection

    connection.status = WarehouseConnectionStatus.PENDING_CONNECTION
    connection.save()
    logger.info(
        "connection.test_event_sent",
        environment__id=connection.environment_id,
        organisation__id=connection.environment.project.organisation_id,
    )
    return connection


def refresh_warehouse_connection_status(
    connection: WarehouseConnection,
    stats: WarehouseEventStats,
) -> WarehouseConnection:
    """Set a pending connection to connected when the warehouse has received at
    least one event. No-op otherwise."""
    if (
        connection.status == WarehouseConnectionStatus.PENDING_CONNECTION
        and stats.total_events_received > 0
    ):
        connection.status = WarehouseConnectionStatus.CONNECTED
        connection.save()
        logger.info(
            "connection.connected",
            environment__id=connection.environment_id,
            organisation__id=connection.environment.project.organisation_id,
        )
    return connection


def annotate_warehouse_event_stats(
    connection: WarehouseConnection,
    environment_key: str,
) -> None:
    """Attach warehouse event stats to a flagsmith connection and update its
    status to match. No-op for non-flagsmith connections or when no warehouse
    is configured; leaves the connection unchanged if the warehouse errors."""
    if (
        connection.warehouse_type != WarehouseType.FLAGSMITH
        or not settings.EXPERIMENTATION_CLICKHOUSE_URL
    ):
        return
    try:
        stats = get_warehouse_event_stats(environment_key)
    except Exception:
        logger.exception(
            "connection.event_stats_unavailable",
            environment__id=connection.environment_id,
        )
        return
    connection.event_stats = stats
    refresh_warehouse_connection_status(connection, stats)
