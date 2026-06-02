from __future__ import annotations

import typing
from functools import lru_cache

from clickhouse_driver import Client
from django.conf import settings
from django.utils import timezone

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from experimentation.constants import EXPERIMENT_FLAG, WAREHOUSE_CONNECTION_FLAG
from integrations.flagsmith.client import get_openfeature_client

if typing.TYPE_CHECKING:
    from experimentation.models import Experiment, Metric, WarehouseConnection
    from organisations.models import Organisation
    from users.models import FFAdminUser


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
    from experimentation.models import VALID_STATUS_TRANSITIONS, ExperimentStatus

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
