from datetime import timedelta

import structlog
from django.conf import settings
from django.utils import timezone
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)
from task_processor.exceptions import TaskBackoffError

from environments.models import Environment, EnvironmentAPIKey
from experimentation import ingestion_sync_service, warehouse_delivery_sync_service
from experimentation.constants import EXTERNAL_WAREHOUSE_EVENTS_TOPIC
from experimentation.models import (
    Experiment,
    ExperimentExposures,
    ExperimentResults,
    WarehouseConnection,
    WarehouseConnectionStatus,
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
        warehouse_delivery_sync_service.remove_warehouse_connection(environment.api_key)
        return

    # Connection details, then destination, then keys. Each step makes the next
    # one safe: the warehouse-delivery service drops events for an environment
    # whose connection it cannot find in Redis, and the ingestion server sends
    # events for an environment with no destination to Flagsmith's own topic.
    if connection.warehouse_type == WarehouseType.FLAGSMITH:
        ingestion_sync_service.delete_ingestion_destination(environment.api_key)
        warehouse_delivery_sync_service.remove_warehouse_connection(environment.api_key)
    else:
        warehouse_delivery_sync_service.publish_warehouse_connection(
            environment.api_key,
            connection_id=connection.id,
            warehouse_type=connection.warehouse_type,
            config=connection.config or {},
            credentials=connection.credentials,
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


@register_recurring_task(run_every=timedelta(minutes=1), timeout=timedelta(minutes=1))
def apply_warehouse_delivery_statuses() -> None:
    """Copies the outcomes the warehouse-delivery service left in Redis onto
    the connections, so the dashboard shows whether a customer's warehouse is
    taking their events. That service never writes to Postgres; this task is
    the only path from it to the connection row."""
    if not settings.INGESTION_REDIS_URL:
        return
    for outcome in warehouse_delivery_sync_service.pop_warehouse_delivery_statuses():
        if outcome.status not in WarehouseConnectionStatus.values:
            logger.warning(
                "delivery_status.unknown",
                connection__id=outcome.connection_id,
                status=outcome.status,
            )
            continue
        updated = WarehouseConnection.objects.filter(id=outcome.connection_id).update(
            status=outcome.status,
            status_detail=outcome.detail[:255] if outcome.detail else None,
        )
        # A connected outcome arrives for every live connection every minute,
        # so only the failures are worth an event.
        if updated and outcome.status == WarehouseConnectionStatus.ERRORED:
            logger.warning(
                "warehouse_connection.delivery_errored",
                connection__id=outcome.connection_id,
                status__detail=outcome.detail,
            )


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
