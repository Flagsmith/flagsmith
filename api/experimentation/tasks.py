import structlog
from django.utils import timezone
from task_processor.decorators import register_task_handler

from environments.models import Environment, EnvironmentAPIKey
from experimentation import ingestion_sync_service
from experimentation.models import Experiment, ExperimentExposures, ExperimentResults
from experimentation.services import compute_exposures_summary, compute_results_summary

logger = structlog.get_logger("experimentation")


@register_task_handler()
def write_environment_ingestion_keys(environment_id: int) -> None:
    environment = (
        Environment.objects.filter(id=environment_id)
        .prefetch_related("api_keys")
        .first()
    )
    if environment is None:
        return

    ingestion_sync_service.set_ingestion_key(
        environment.api_key,
        environment_key=environment.api_key,
    )
    for api_key in environment.api_keys.all():
        if api_key.is_valid:
            ingestion_sync_service.set_ingestion_key(
                api_key.key,
                environment_key=environment.api_key,
                expires_at=api_key.expires_at,
            )


@register_task_handler()
def remove_environment_ingestion_keys(environment_id: int) -> None:
    environment = (
        Environment.objects.filter(id=environment_id)
        .prefetch_related("api_keys")
        .first()
    )
    if environment is None:
        return

    ingestion_sync_service.delete_ingestion_key(environment.api_key)
    for api_key in environment.api_keys.all():
        ingestion_sync_service.delete_ingestion_key(api_key.key)


@register_task_handler()
def write_environment_ingestion_key(environment_api_key_id: int) -> None:
    api_key = (
        EnvironmentAPIKey.objects.select_related("environment")
        .filter(id=environment_api_key_id)
        .first()
    )
    if api_key is None:
        return

    if api_key.is_valid:
        ingestion_sync_service.set_ingestion_key(
            api_key.key,
            environment_key=api_key.environment.api_key,
            expires_at=api_key.expires_at,
        )
    else:
        ingestion_sync_service.delete_ingestion_key(api_key.key)


@register_task_handler()
def remove_environment_ingestion_key(key: str) -> None:
    ingestion_sync_service.delete_ingestion_key(key)


@register_task_handler()
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
            environment_key=experiment.environment.api_key,
            feature_name=experiment.feature.name,
            window_start=experiment.started_at,
            window_end=as_of,
        )
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
        return

    exposures.record_refresh(summary, as_of)


@register_task_handler()
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
    except Exception as exc:
        results.record_failure()
        logger.error(
            "results.compute_failed",
            exc_info=exc,
            experiment__id=experiment.id,
            environment__id=experiment.environment_id,
            organisation__id=experiment.environment.project.organisation_id,
        )
        return

    results.record_refresh(summary, as_of)
