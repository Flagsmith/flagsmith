from __future__ import annotations

import typing
from functools import lru_cache

import structlog
from clickhouse_driver import Client
from clickhouse_driver.util.helpers import parse_url
from django.conf import settings
from django.utils import timezone

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from experimentation.constants import (
    EXPERIMENT_FLAG,
    EXPOSURE_EVENT_NAME,
    MULTIPLE_VARIANT_KEY,
    WAREHOUSE_CONNECTION_FLAG,
)
from experimentation.dataclasses import ExposureBucket, WarehouseEventStats
from experimentation.models import (
    VALID_STATUS_TRANSITIONS,
    ExperimentStatus,
    WarehouseConnectionStatus,
    WarehouseType,
)
from integrations.flagsmith.client import get_openfeature_client

if typing.TYPE_CHECKING:
    from datetime import datetime

    from experimentation.models import Experiment, Metric, WarehouseConnection
    from experimentation.types import ExposureGranularity
    from organisations.models import Organisation
    from users.models import FFAdminUser

logger = structlog.get_logger("warehouse")

CLICKHOUSE_CONNECT_TIMEOUT_SECONDS = 5
CLICKHOUSE_QUERY_TIMEOUT_SECONDS = 30


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
    `events` table unqualified. Connect and query timeouts are bounded unless the
    DSN overrides them.
    """
    host, kwargs = parse_url(settings.EXPERIMENTATION_CLICKHOUSE_URL)
    kwargs.setdefault("connect_timeout", CLICKHOUSE_CONNECT_TIMEOUT_SECONDS)
    kwargs.setdefault("send_receive_timeout", CLICKHOUSE_QUERY_TIMEOUT_SECONDS)
    return Client(host, **kwargs)


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


# Identities are reduced to their first exposure, so at-least-once duplicate
# delivery cannot inflate unit counts, and identities seen in more than one
# variant are quarantined under the sentinel variant. Bucketing first exposures
# powers the cumulative time series.
EXPOSURE_BUCKETS_QUERY = """
WITH exposures AS (
    SELECT
        identifier,
        if(uniqExact(value) > 1, %(multiple_variant)s, any(value)) AS variant,
        min(timestamp) AS first_exposure,
        max(timestamp) AS last_exposure
    FROM events
    WHERE environment_key = %(environment_key)s
        AND event = %(exposure_event)s
        AND feature_name = %(feature_name)s
        AND timestamp >= %(window_start)s
        AND timestamp <= %(window_end)s
    GROUP BY identifier
)
SELECT
    variant,
    {bucket_function}(first_exposure) AS bucket,
    count() AS new_units,
    min(first_exposure) AS first_exposure,
    max(last_exposure) AS last_exposure
FROM exposures
GROUP BY variant, bucket
ORDER BY bucket
"""

_EXPOSURE_BUCKET_FUNCTIONS: dict[str, str] = {
    "hour": "toStartOfHour",
    "day": "toStartOfDay",
}


def get_exposure_buckets(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
    granularity: ExposureGranularity,
) -> list[ExposureBucket]:
    """Return an experiment's exposures per variant per time bucket."""
    rows = _get_clickhouse_client().execute(
        EXPOSURE_BUCKETS_QUERY.format(
            bucket_function=_EXPOSURE_BUCKET_FUNCTIONS[granularity]
        ),
        {
            "environment_key": environment_key,
            "exposure_event": EXPOSURE_EVENT_NAME,
            "feature_name": feature_name,
            "multiple_variant": MULTIPLE_VARIANT_KEY,
            "window_start": window_start,
            "window_end": window_end,
        },
    )
    return [
        ExposureBucket(
            variant=variant,
            bucket=bucket,
            new_units=int(new_units),
            first_exposure=first_exposure,
            last_exposure=last_exposure,
        )
        for variant, bucket, new_units, first_exposure, last_exposure in rows
    ]


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


def create_metric_audit_log(
    metric: Metric,
    user: FFAdminUser,
    *,
    action: str,
) -> None:
    AuditLog.objects.create(
        environment=metric.environment,
        project=metric.environment.project,
        **_resolve_audit_log_author(user),
        related_object_id=metric.id,
        related_object_type=RelatedObjectType.METRIC.name,
        log=f"Metric '{metric.name}' {action}",
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
    connection.save(update_fields=["status"])
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
        connection.save(update_fields=["status"])
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
    """Attach live warehouse event stats to a flagsmith connection. No-op for
    non-flagsmith connections or when no warehouse is configured; leaves stats
    unset when the warehouse is unreachable. Read-only: never changes status."""
    if (
        connection.warehouse_type != WarehouseType.FLAGSMITH
        or not settings.EXPERIMENTATION_CLICKHOUSE_URL
    ):
        return
    try:
        connection.event_stats = get_warehouse_event_stats(environment_key)
    except Exception:
        return
