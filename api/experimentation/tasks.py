from datetime import timedelta

import structlog
from django.utils import timezone
from task_processor.decorators import register_task_handler
from task_processor.exceptions import TaskBackoffError

from environments.models import Environment, EnvironmentAPIKey
from experimentation import ingestion_sync_service, warehouse_delivery_sync_service
from experimentation.constants import EXTERNAL_WAREHOUSE_EVENTS_TOPIC
from experimentation.models import (
    Experiment,
    ExperimentExposures,
    ExperimentResults,
    WarehouseConnection,
    WarehouseType,
)
from experimentation.services import (
    compute_exposures_summary,
    compute_results_summary,
)

COMPUTE_TASK_TIMEOUT = timedelta(minutes=3)

logger = structlog.get_logger("experimentation")


@register_task_handler()
def sync_environment_ingestion(environment_id: int) -> None:
    """Bring the ingestion server's keys and destination for an environment in
    line with its active warehouse connection, or remove them when it has none."""
    # Deleting an environment soft-deletes its connection, which enqueues this
    # task, so the environment has to be found even once it is deleted.
    environment = (
        Environment.objects.all_with_deleted()
        .filter(id=environment_id)
        .prefetch_related("api_keys")
        .first()
    )
    if environment is None:
        return

    connection = (
        None if environment.deleted_at else environment.warehouse_connections.first()
    )
    if connection is None:
        ingestion_sync_service.delete_ingestion_key(environment.api_key)
        for api_key in environment.api_keys.all():
            ingestion_sync_service.delete_ingestion_key(api_key.key)
        ingestion_sync_service.delete_ingestion_destination(environment.api_key)
        # The connection is gone, so include deleted ones to find its id.
        connection_ids = (
            WarehouseConnection.objects.all_with_deleted()
            .filter(environment_id=environment.id)
            .values_list("id", flat=True)
        )
        warehouse_delivery_sync_service.remove_warehouse_connection(environment.api_key)
        warehouse_delivery_sync_service.delete_warehouse_delivery_statuses(
            list(connection_ids)
        )
        return

    # Connection details, then destination, then keys. Each step makes the next
    # one safe: the warehouse-delivery service drops events for an environment
    # whose connection it cannot find in Redis, and the ingestion server sends
    # events for an environment with no destination to Flagsmith's own topic.
    if connection.warehouse_type == WarehouseType.FLAGSMITH:
        ingestion_sync_service.delete_ingestion_destination(environment.api_key)
        warehouse_delivery_sync_service.remove_warehouse_connection(environment.api_key)
        warehouse_delivery_sync_service.delete_warehouse_delivery_statuses(
            [connection.id]
        )
    else:
        warehouse_delivery_sync_service.publish_warehouse_connection(
            environment.api_key,
            connection_id=connection.id,
            warehouse_type=connection.warehouse_type,
            config=connection.config or {},
            credentials=connection.credentials,
        )
        # Its last outcome was about the details just replaced.
        warehouse_delivery_sync_service.delete_warehouse_delivery_statuses(
            [connection.id]
        )
        ingestion_sync_service.set_ingestion_destination(
            environment.api_key,
            topic=EXTERNAL_WAREHOUSE_EVENTS_TOPIC,
        )
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
