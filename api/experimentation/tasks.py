from datetime import timedelta

import structlog
from django.utils import timezone
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from environments.models import Environment, EnvironmentAPIKey
from experimentation import ingestion_sync_service, warehouse_delivery_service
from experimentation.constants import DELIVERY_INTERVAL
from experimentation.metrics import (
    flagsmith_experimentation_warehouse_delivery_objects_total,
    flagsmith_experimentation_warehouse_delivery_runs_total,
)
from experimentation.models import (
    Experiment,
    ExperimentExposures,
    ExperimentResults,
    WarehouseConnection,
    WarehouseType,
)
from experimentation.organisation_ingestion_service import (
    disable_ingestion_for_organisation,
    enable_ingestion_for_organisation,
)
from experimentation.services import (
    compute_exposures_summary,
    compute_results_summary,
    mark_warehouse_delivery_failed,
    mark_warehouse_delivery_succeeded,
)

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
    ingestion_sync_service.delete_ingestion_destination(environment.api_key)


@register_task_handler()
def provision_external_warehouse_ingestion_infrastructure(environment_id: int) -> None:
    environment = (
        Environment.objects.select_related("project__organisation")
        .filter(id=environment_id)
        .first()
    )
    if environment is None:
        return

    infrastructure = enable_ingestion_for_organisation(environment.project.organisation)
    if not infrastructure.stream_name:
        raise RuntimeError("Provisioned ingestion infrastructure has no stream name")
    # Set the destination before publishing the ingestion keys: the keys gate
    # the pipeline, so a key without a destination would route events to the
    # default stream until this write lands.
    ingestion_sync_service.set_ingestion_destination(
        environment.api_key,
        stream_name=infrastructure.stream_name,
    )
    write_environment_ingestion_keys(environment_id)


@register_task_handler()
def teardown_organisation_ingestion_infrastructure(organisation_id: int) -> None:
    disable_ingestion_for_organisation(organisation_id)


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


@register_recurring_task(run_every=DELIVERY_INTERVAL)
def deliver_events_to_external_warehouses() -> None:
    connection_ids = WarehouseConnection.objects.filter(
        warehouse_type=WarehouseType.CLICKHOUSE,
    ).values_list("id", flat=True)
    for connection_id in connection_ids:
        deliver_events_for_connection.delay(kwargs={"connection_id": connection_id})


@register_task_handler(timeout=timedelta(minutes=9))
def deliver_events_for_connection(connection_id: int) -> None:
    connection = (
        WarehouseConnection.objects.select_related(
            "environment__project__organisation__ingestion_infrastructure",
        )
        .filter(id=connection_id)
        .first()
    )
    if connection is None:
        return

    organisation = connection.environment.project.organisation
    infrastructure = getattr(organisation, "ingestion_infrastructure", None)
    if infrastructure is None or not infrastructure.bucket_name:
        return

    log = logger.bind(
        environment__id=connection.environment_id,
        organisation__id=organisation.id,
    )
    bucket_name = infrastructure.bucket_name
    pending = warehouse_delivery_service.list_pending_objects(
        bucket_name,
        environment_key=connection.environment.api_key,
    )
    if not pending:
        return

    delivered_count = rejected_count = rows_count = 0
    try:
        with warehouse_delivery_service.delivery_client(connection) as client:
            for s3_key in pending:
                try:
                    rows_count += warehouse_delivery_service.deliver_object(
                        client,
                        bucket_name,
                        s3_key,
                    )
                except warehouse_delivery_service.ObjectRejectedError:
                    # This object's contents are the problem; the ones behind
                    # it are still deliverable.
                    warehouse_delivery_service.move_object(
                        bucket_name,
                        s3_key,
                        to_prefix=warehouse_delivery_service.FAILED_PREFIX,
                    )
                    rejected_count += 1
                    flagsmith_experimentation_warehouse_delivery_objects_total.labels(
                        result="rejected"
                    ).inc()
                    log.warning("warehouse_delivery.object_rejected", exc_info=True)
                    continue
                warehouse_delivery_service.move_object(
                    bucket_name,
                    s3_key,
                    to_prefix=warehouse_delivery_service.ARCHIVE_PREFIX,
                )
                delivered_count += 1
                flagsmith_experimentation_warehouse_delivery_objects_total.labels(
                    result="delivered"
                ).inc()
    except Exception as exc:
        # The warehouse itself is unusable; deliver nothing, leave every
        # remaining object in place for the next run, and surface the
        # breakage on the connection.
        mark_warehouse_delivery_failed(
            connection,
            detail=warehouse_delivery_service.describe_delivery_error(exc),
        )
        flagsmith_experimentation_warehouse_delivery_runs_total.labels(
            result="failure"
        ).inc()
        log.error("warehouse_delivery.failed", exc_info=exc)
        return

    mark_warehouse_delivery_succeeded(connection)
    flagsmith_experimentation_warehouse_delivery_runs_total.labels(
        result="success"
    ).inc()
    log.info(
        "warehouse_delivery.completed",
        objects__count=delivered_count,
        objects__rejected_count=rejected_count,
        rows__count=rows_count,
    )


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
