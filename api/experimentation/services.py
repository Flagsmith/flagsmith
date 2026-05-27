from __future__ import annotations

import typing

from django.utils import timezone

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from experimentation.constants import EXPERIMENT_FLAG, WAREHOUSE_CONNECTION_FLAG
from integrations.flagsmith.client import get_openfeature_client

if typing.TYPE_CHECKING:
    from experimentation.models import Experiment, WarehouseConnection
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


def _resolve_audit_log_author(
    user: FFAdminUser,
) -> dict[str, int | None]:
    if getattr(user, "is_master_api_key_user", False):
        return {"author_id": None, "master_api_key_id": user.key.id}  # type: ignore[union-attr]
    return {"author_id": user.pk, "master_api_key_id": None}  # type: ignore[union-attr]


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
