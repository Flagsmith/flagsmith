from datetime import timedelta

import structlog
from django.conf import settings
from django.utils import timezone
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from experimentation import ingestion_sync_service
from experimentation.metrics import (
    flagsmith_experimentation_exposures_computation_duration_seconds,
    flagsmith_experimentation_exposures_computations_total,
)

logger = structlog.get_logger("experimentation")


@register_task_handler()
def add_environment_key_to_ingestion(environment_api_key: str) -> None:
    ingestion_sync_service.set_environment_key(environment_api_key)


@register_task_handler()
def delete_environment_key_from_ingestion(environment_api_key: str) -> None:
    ingestion_sync_service.delete_environment_key(environment_api_key)


@register_task_handler()
def compute_experiment_exposures(experiment_id: int) -> None:
    # Imported lazily: models imports this module at load time.
    from experimentation.models import Experiment, ExperimentExposures
    from experimentation.services import compute_exposures_summary

    experiment = Experiment.objects.select_related(
        "environment__project",
        "feature",
    ).get(id=experiment_id)
    if not experiment.started_at:
        return

    log = logger.bind(
        experiment__id=experiment.id,
        environment__id=experiment.environment_id,
        organisation__id=experiment.environment.project.organisation_id,
    )
    exposures, _ = ExperimentExposures.objects.get_or_create(experiment=experiment)
    as_of = experiment.ended_at or timezone.now()
    try:
        with flagsmith_experimentation_exposures_computation_duration_seconds.time():
            summary = compute_exposures_summary(
                environment_key=experiment.environment.api_key,
                feature_name=experiment.feature.name,
                window_start=experiment.started_at,
                window_end=as_of,
            )
    except Exception as exc:
        exposures.record_failure()
        flagsmith_experimentation_exposures_computations_total.labels(
            result="failure"
        ).inc()
        log.error("exposures.compute_failed", exc_info=exc)
        return

    exposures.record_refresh(summary, as_of)
    flagsmith_experimentation_exposures_computations_total.labels(
        result="success"
    ).inc()
    log.info(
        "exposures.computed",
        identities__count=sum(
            sum(point.new_identities.values()) for point in summary.timeseries.points
        ),
        excluded_identities__count=summary.excluded_identities,
    )


@register_recurring_task(
    run_every=timedelta(minutes=settings.EXPERIMENTATION_EXPOSURES_REFRESH_MINUTES),
)
def refresh_running_experiment_exposures() -> None:
    # Imported lazily: models imports this module at load time.
    from experimentation.models import Experiment, ExperimentStatus

    if not settings.EXPERIMENTATION_CLICKHOUSE_URL:
        return

    for experiment_id in Experiment.objects.filter(
        status=ExperimentStatus.RUNNING
    ).values_list("id", flat=True):
        compute_experiment_exposures.delay(kwargs={"experiment_id": experiment_id})
