from datetime import timedelta

import structlog
from django.utils import timezone
from task_processor.decorators import register_task_handler
from task_processor.exceptions import TaskBackoffError

from experimentation.models import (
    Experiment,
    ExperimentExposures,
    ExperimentResults,
)
from experimentation.services import (
    compute_exposures_summary,
    compute_results_summary,
)
from experimentation.warehouses.exceptions import UnsupportedWarehouseOperation

COMPUTE_TASK_TIMEOUT = timedelta(minutes=3)

logger = structlog.get_logger("experimentation")


@register_task_handler(timeout=COMPUTE_TASK_TIMEOUT)
def compute_experiment_exposures(experiment_id: int) -> None:
    experiment = (
        Experiment.objects.select_related("environment__project", "feature")
        .filter(id=experiment_id)
        .first()
    )
    if experiment is None or not experiment.started_at:
        return

    exposures, _ = ExperimentExposures.objects.get_or_create(experiment=experiment)
    if exposures.is_final:
        return

    as_of = experiment.ended_at or timezone.now()
    try:
        summary = compute_exposures_summary(
            experiment,
            window_start=experiment.started_at,
            window_end=as_of,
        )
    except UnsupportedWarehouseOperation:
        exposures.record_failure()
        logger.warning(
            "exposures.compute_unsupported",
            experiment__id=experiment.id,
            environment__id=experiment.environment_id,
            organisation__id=experiment.environment.project.organisation_id,
            warehouse__type=_warehouse_type(experiment),
        )
        return
    except Exception as exc:
        exposures.record_failure()
        logger.error(
            "exposures.compute_failed",
            exc_info=exc,
            experiment__id=experiment.id,
            feature__id=experiment.feature_id,
            environment__id=experiment.environment_id,
            organisation__id=experiment.environment.project.organisation_id,
        )
        if isinstance(exc, OSError):
            raise TaskBackoffError() from exc
        return

    exposures.record_refresh(summary, as_of)


@register_task_handler(timeout=COMPUTE_TASK_TIMEOUT)
def compute_experiment_results(experiment_id: int) -> None:
    experiment = (
        Experiment.objects.select_related("environment__project", "feature")
        .filter(id=experiment_id)
        .first()
    )
    if experiment is None or not experiment.started_at:
        return

    results, _ = ExperimentResults.objects.get_or_create(experiment=experiment)
    if results.is_final:
        return

    as_of = experiment.ended_at or timezone.now()
    try:
        summary = compute_results_summary(
            experiment,
            window_start=experiment.started_at,
            window_end=as_of,
        )
    except UnsupportedWarehouseOperation:
        results.record_failure()
        logger.warning(
            "results.compute_unsupported",
            experiment__id=experiment.id,
            environment__id=experiment.environment_id,
            organisation__id=experiment.environment.project.organisation_id,
            warehouse__type=_warehouse_type(experiment),
        )
        return
    except Exception as exc:
        results.record_failure()
        logger.error(
            "results.compute_failed",
            exc_info=exc,
            experiment__id=experiment.id,
            environment__id=experiment.environment_id,
            organisation__id=experiment.environment.project.organisation_id,
        )
        if isinstance(exc, OSError):
            raise TaskBackoffError() from exc
        return

    results.record_refresh(summary, as_of)


def _warehouse_type(experiment: Experiment) -> str | None:
    connection = experiment.environment.warehouse_connections.only(
        "warehouse_type"
    ).first()
    return connection.warehouse_type if connection else None
