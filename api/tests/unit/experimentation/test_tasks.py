import itertools
from collections.abc import Iterator
from dataclasses import asdict
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from typing import Any

import boto3
import pytest
from clickhouse_connect.driver.exceptions import DatabaseError
from django.utils import timezone
from freezegun import freeze_time
from moto import mock_s3  # type: ignore[import-untyped]
from prometheus_client import REGISTRY
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment, EnvironmentAPIKey
from experimentation import warehouse_delivery_service
from experimentation.dataclasses import (
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
    IngestionInfrastructure,
    MetricResult,
    ResultsSummary,
)
from experimentation.models import (
    Experiment,
    ExperimentExposures,
    ExperimentResults,
    ExperimentStatus,
    IngestionInfrastructureStatus,
    OrganisationIngestionInfrastructure,
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseDeliveryLog,
    WarehouseDeliveryOutcome,
    WarehouseType,
)
from experimentation.stats import VariantStats
from experimentation.tasks import (
    compute_experiment_exposures,
    compute_experiment_results,
    deliver_events_for_connection,
    deliver_events_to_external_warehouses,
    provision_external_warehouse_ingestion_infrastructure,
    remove_environment_ingestion_key,
    remove_environment_ingestion_keys,
    teardown_organisation_ingestion_infrastructure,
    write_environment_ingestion_key,
    write_environment_ingestion_keys,
)
from organisations.models import Organisation
from projects.models import Project


def test_write_environment_ingestion_keys__valid_keys__whitelists_client_and_server(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given an environment with a valid server-side key, an inactive one, and an
    # expired one
    valid_key = EnvironmentAPIKey.objects.create(
        environment=environment,
        name="active",
        expires_at=timezone.now() + timedelta(days=30),
    )
    EnvironmentAPIKey.objects.create(
        environment=environment, name="inactive", active=False
    )
    EnvironmentAPIKey.objects.create(
        environment=environment,
        name="expired",
        expires_at=timezone.now() - timedelta(days=1),
    )
    mock_set = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_ingestion_key",
    )

    # When
    write_environment_ingestion_keys(environment_id=environment.id)

    # Then only the client key and the valid server-side key are whitelisted
    assert mock_set.call_args_list == [
        mocker.call(environment.api_key, environment_key=environment.api_key),
        mocker.call(
            valid_key.key,
            environment_key=environment.api_key,
            expires_at=valid_key.expires_at,
        ),
    ]


def test_write_environment_ingestion_keys__missing_environment__does_nothing(
    db: None,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_set = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_ingestion_key",
    )

    # When
    write_environment_ingestion_keys(environment_id=404404)

    # Then
    mock_set.assert_not_called()


def test_remove_environment_ingestion_keys__client_and_server_keys__all_removed(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given an environment with active and inactive server-side keys
    active_key = EnvironmentAPIKey.objects.create(
        environment=environment, name="active"
    )
    inactive_key = EnvironmentAPIKey.objects.create(
        environment=environment, name="inactive", active=False
    )
    mock_delete = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.delete_ingestion_key",
    )
    mock_delete_destination = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.delete_ingestion_destination",
    )

    # When
    remove_environment_ingestion_keys(environment_id=environment.id)

    # Then the client key and every server-side key are removed regardless of state
    assert mock_delete.call_args_list == [
        mocker.call(environment.api_key),
        mocker.call(active_key.key),
        mocker.call(inactive_key.key),
    ]
    # And the environment's destination routing is cleared
    mock_delete_destination.assert_called_once_with(environment.api_key)


def test_remove_environment_ingestion_keys__missing_environment__does_nothing(
    db: None,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_delete = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.delete_ingestion_key",
    )

    # When
    remove_environment_ingestion_keys(environment_id=404404)

    # Then
    mock_delete.assert_not_called()


def test_write_environment_ingestion_key__valid_key__whitelists_it(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given a valid server-side key
    api_key = EnvironmentAPIKey.objects.create(
        environment=environment,
        name="active",
        expires_at=timezone.now() + timedelta(days=30),
    )
    mock_set = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_ingestion_key",
    )
    mock_delete = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.delete_ingestion_key",
    )

    # When
    write_environment_ingestion_key(environment_api_key_id=api_key.id)

    # Then it is whitelisted under the environment's client key
    mock_set.assert_called_once_with(
        api_key.key,
        environment_key=environment.api_key,
        expires_at=api_key.expires_at,
    )
    mock_delete.assert_not_called()


def test_write_environment_ingestion_key__invalid_key__removes_it(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given an inactive server-side key
    api_key = EnvironmentAPIKey.objects.create(
        environment=environment, name="inactive", active=False
    )
    mock_set = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_ingestion_key",
    )
    mock_delete = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.delete_ingestion_key",
    )

    # When
    write_environment_ingestion_key(environment_api_key_id=api_key.id)

    # Then it is removed from the whitelist
    mock_delete.assert_called_once_with(api_key.key)
    mock_set.assert_not_called()


def test_write_environment_ingestion_key__missing_key__does_nothing(
    db: None,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_set = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_ingestion_key",
    )
    mock_delete = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.delete_ingestion_key",
    )

    # When
    write_environment_ingestion_key(environment_api_key_id=404404)

    # Then
    mock_set.assert_not_called()
    mock_delete.assert_not_called()


def test_remove_environment_ingestion_key__valid_key__calls_service(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_delete = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.delete_ingestion_key",
    )

    # When
    remove_environment_ingestion_key(key="ser.test-key-001")

    # Then
    mock_delete.assert_called_once_with("ser.test-key-001")


def _summary() -> ExposuresSummary:
    return ExposuresSummary(
        excluded_identities=1,
        timeseries=ExposuresTimeseries(
            granularity="hour",
            points=[
                ExposuresTimeseriesPoint(
                    bucket="2026-06-01T00:00:00+00:00",
                    new_identities={"control": 6, "variant_a": 4},
                )
            ],
        ),
    )


@freeze_time("2026-06-11T12:00:00Z")
def test_compute_experiment_exposures__running_experiment__stores_summary(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given a running experiment and a warehouse responding with a summary
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_exposures_summary",
        return_value=_summary(),
    )

    # When
    compute_experiment_exposures(experiment_id=experiment.id)

    # Then the full window up to now is computed and stored on the row
    mock_compute.assert_called_once_with(
        environment_key=experiment.environment.api_key,
        feature_name=experiment.feature.name,
        window_start=experiment.started_at,
        window_end=timezone.now(),
    )
    exposures = ExperimentExposures.objects.get(experiment=experiment)
    assert exposures.payload == asdict(_summary())
    assert exposures.as_of == timezone.now()
    assert exposures.last_error_at is None


def test_compute_experiment_exposures__completed_experiment__window_ends_at_ended_at(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given a completed experiment
    experiment.status = ExperimentStatus.COMPLETED
    experiment.started_at = datetime(2026, 6, 1, tzinfo=dt_timezone.utc)
    experiment.ended_at = datetime(2026, 6, 8, tzinfo=dt_timezone.utc)
    experiment.save()
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_exposures_summary",
        return_value=_summary(),
    )

    # When
    compute_experiment_exposures(experiment_id=experiment.id)

    # Then the window is frozen at the experiment's end
    mock_compute.assert_called_once_with(
        environment_key=experiment.environment.api_key,
        feature_name=experiment.feature.name,
        window_start=experiment.started_at,
        window_end=experiment.ended_at,
    )
    exposures = ExperimentExposures.objects.get(experiment=experiment)
    assert exposures.as_of == experiment.ended_at


def test_compute_experiment_exposures__warehouse_error__records_failure(
    experiment: Experiment,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given a running experiment whose row holds a previously computed payload
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    as_of = timezone.now()
    ExperimentExposures.objects.create(
        experiment=experiment,
        as_of=as_of,
        payload=asdict(_summary()),
    )
    mocker.patch(
        "experimentation.tasks.compute_exposures_summary",
        side_effect=Exception("warehouse unreachable"),
    )

    # When
    compute_experiment_exposures(experiment_id=experiment.id)

    # Then the failure is recorded and the last good payload survives
    exposures = ExperimentExposures.objects.get(experiment=experiment)
    assert exposures.last_error_at is not None
    assert exposures.payload == asdict(_summary())
    assert exposures.as_of == as_of
    # And the failure is logged for operators
    assert log.has(
        "exposures.compute_failed",
        level="error",
        experiment__id=experiment.id,
        environment__id=experiment.environment_id,
        organisation__id=experiment.environment.project.organisation_id,
    )


def test_compute_experiment_exposures__not_started_experiment__skips(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given a created experiment that has never started
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_exposures_summary",
    )

    # When
    compute_experiment_exposures(experiment_id=experiment.id)

    # Then nothing is queried or stored
    mock_compute.assert_not_called()
    assert not ExperimentExposures.objects.filter(experiment=experiment).exists()


def test_compute_experiment_exposures__final_row__skips_without_recompute(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given a completed experiment whose row already covers the full window
    experiment.status = ExperimentStatus.COMPLETED
    experiment.started_at = datetime(2026, 6, 1, tzinfo=dt_timezone.utc)
    experiment.ended_at = datetime(2026, 6, 8, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentExposures.objects.create(
        experiment=experiment,
        as_of=experiment.ended_at,
        payload=asdict(_summary()),
    )
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_exposures_summary",
    )

    # When
    compute_experiment_exposures(experiment_id=experiment.id)

    # Then the final payload is left untouched regardless of the caller
    mock_compute.assert_not_called()
    exposures = ExperimentExposures.objects.get(experiment=experiment)
    assert exposures.payload == asdict(_summary())


def test_compute_experiment_exposures__experiment_deleted_after_enqueue__skips(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given the experiment is deleted between enqueue and execution
    experiment_id = experiment.id
    experiment.delete()
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_exposures_summary",
    )

    # When
    compute_experiment_exposures(experiment_id=experiment_id)

    # Then the task exits without raising into the task processor
    mock_compute.assert_not_called()


def _results_summary() -> ResultsSummary:
    return ResultsSummary(
        srm_p_value=0.42,
        metrics=[
            MetricResult(
                metric_id=7,
                variants={
                    "control": VariantStats(n=1000, sum=100.0, sum_squares=100.0)
                },
                inference={},
            )
        ],
    )


@freeze_time("2026-06-11T12:00:00Z")
def test_compute_experiment_results__running_experiment__stores_summary(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given a running experiment and a warehouse responding with a summary
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_results_summary",
        return_value=_results_summary(),
    )

    # When
    compute_experiment_results(experiment_id=experiment.id)

    # Then the full window up to now is computed and stored on the row
    mock_compute.assert_called_once_with(
        experiment,
        window_start=experiment.started_at,
        window_end=timezone.now(),
    )
    results = ExperimentResults.objects.get(experiment=experiment)
    assert results.payload == asdict(_results_summary())
    assert results.as_of == timezone.now()
    assert results.last_error_at is None


def test_compute_experiment_results__completed_experiment__window_ends_at_ended_at(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given a completed experiment
    experiment.status = ExperimentStatus.COMPLETED
    experiment.started_at = datetime(2026, 6, 1, tzinfo=dt_timezone.utc)
    experiment.ended_at = datetime(2026, 6, 8, tzinfo=dt_timezone.utc)
    experiment.save()
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_results_summary",
        return_value=_results_summary(),
    )

    # When
    compute_experiment_results(experiment_id=experiment.id)

    # Then the window is frozen at the experiment's end
    mock_compute.assert_called_once_with(
        experiment,
        window_start=experiment.started_at,
        window_end=experiment.ended_at,
    )
    results = ExperimentResults.objects.get(experiment=experiment)
    assert results.as_of == experiment.ended_at


def test_compute_experiment_results__warehouse_error__records_failure(
    experiment: Experiment,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given a running experiment whose row holds a previously computed payload
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    as_of = timezone.now()
    ExperimentResults.objects.create(
        experiment=experiment,
        as_of=as_of,
        payload=asdict(_results_summary()),
    )
    exc = Exception("warehouse unreachable")
    mocker.patch(
        "experimentation.tasks.compute_results_summary",
        side_effect=exc,
    )

    # When
    compute_experiment_results(experiment_id=experiment.id)

    # Then the failure is recorded and the last good payload survives
    results = ExperimentResults.objects.get(experiment=experiment)
    assert results.last_error_at is not None
    assert results.payload == asdict(_results_summary())
    assert results.as_of == as_of
    # And exactly one failure event is logged for operators, carrying the
    # exception so the traceback reaches the logs
    assert log.events == [
        {
            "event": "results.compute_failed",
            "level": "error",
            "exc_info": exc,
            "experiment__id": experiment.id,
            "environment__id": experiment.environment_id,
            "organisation__id": experiment.environment.project.organisation_id,
        }
    ]


def test_compute_experiment_results__not_started_experiment__skips(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given a created experiment that has never started
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_results_summary",
    )

    # When
    compute_experiment_results(experiment_id=experiment.id)

    # Then nothing is queried or stored
    mock_compute.assert_not_called()
    assert not ExperimentResults.objects.filter(experiment=experiment).exists()


def test_compute_experiment_results__final_row__skips_without_recompute(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given a completed experiment whose row already covers the full window
    experiment.status = ExperimentStatus.COMPLETED
    experiment.started_at = datetime(2026, 6, 1, tzinfo=dt_timezone.utc)
    experiment.ended_at = datetime(2026, 6, 8, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentResults.objects.create(
        experiment=experiment,
        as_of=experiment.ended_at,
        payload=asdict(_results_summary()),
    )
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_results_summary",
    )

    # When
    compute_experiment_results(experiment_id=experiment.id)

    # Then the final payload is left untouched regardless of the caller
    mock_compute.assert_not_called()
    results = ExperimentResults.objects.get(experiment=experiment)
    assert results.payload == asdict(_results_summary())


def test_compute_experiment_results__experiment_deleted_after_enqueue__skips(
    experiment: Experiment,
    mocker: MockerFixture,
) -> None:
    # Given the experiment is deleted between enqueue and execution
    experiment_id = experiment.id
    experiment.delete()
    mock_compute = mocker.patch(
        "experimentation.tasks.compute_results_summary",
    )

    # When
    compute_experiment_results(experiment_id=experiment_id)

    # Then the task exits without raising into the task processor
    mock_compute.assert_not_called()


def test_provision_external_warehouse_ingestion_infrastructure__valid_environment__provisions_and_syncs_keys(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    provision = mocker.patch(
        "experimentation.organisation_ingestion_service"
        ".provision_ingestion_infrastructure",
        return_value=IngestionInfrastructure(
            bucket_name="flagsmith-events-lake-org-1-123456789012-eu-west-2-an",
            stream_name="events-ingestion-org-1",
        ),
    )
    set_ingestion_key = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_ingestion_key",
    )
    set_ingestion_destination = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_ingestion_destination",
    )

    # When
    provision_external_warehouse_ingestion_infrastructure(environment_id=environment.id)

    # Then the org infrastructure is provisioned and the environment keys synced
    provision.assert_called_once_with(environment.project.organisation_id)
    assert OrganisationIngestionInfrastructure.objects.filter(
        organisation=environment.project.organisation,
        status=IngestionInfrastructureStatus.CREATED,
    ).exists()
    set_ingestion_key.assert_called_once_with(
        environment.api_key, environment_key=environment.api_key
    )
    # And the environment is routed to the org's provisioned stream
    set_ingestion_destination.assert_called_once_with(
        environment.api_key, stream_name="events-ingestion-org-1"
    )


@pytest.mark.parametrize("stream_name", [None, ""], ids=["none", "blank"])
def test_provision_external_warehouse_ingestion_infrastructure__no_stream_name__raises(
    environment: Environment,
    mocker: MockerFixture,
    stream_name: str | None,
) -> None:
    # Given provisioning returns infrastructure without a usable stream name
    infrastructure = OrganisationIngestionInfrastructure(
        organisation=environment.project.organisation,
        status=IngestionInfrastructureStatus.CREATED,
        stream_name=stream_name,
    )
    mocker.patch(
        "experimentation.tasks.enable_ingestion_for_organisation",
        return_value=infrastructure,
    )
    set_ingestion_destination = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_ingestion_destination",
    )
    write_keys = mocker.patch(
        "experimentation.tasks.write_environment_ingestion_keys",
    )

    # When / Then the task fails loudly without seeding a broken destination
    with pytest.raises(RuntimeError, match="no stream name"):
        provision_external_warehouse_ingestion_infrastructure(
            environment_id=environment.id
        )
    set_ingestion_destination.assert_not_called()
    write_keys.assert_not_called()


def test_provision_external_warehouse_ingestion_infrastructure__missing_environment__does_nothing(
    db: None,
    mocker: MockerFixture,
) -> None:
    # Given
    provision = mocker.patch(
        "experimentation.organisation_ingestion_service"
        ".provision_ingestion_infrastructure",
    )

    # When
    provision_external_warehouse_ingestion_infrastructure(environment_id=999999)

    # Then
    provision.assert_not_called()
    assert not OrganisationIngestionInfrastructure.objects.exists()


def test_teardown_organisation_ingestion_infrastructure__created_infrastructure__deprovisions(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    OrganisationIngestionInfrastructure.objects.create(
        organisation=organisation,
        status=IngestionInfrastructureStatus.CREATED,
        bucket_name="flagsmith-events-lake-org-1-123456789012-eu-west-2-an",
        stream_name="events-ingestion-org-1",
    )
    deprovision = mocker.patch(
        "experimentation.organisation_ingestion_service"
        ".deprovision_ingestion_infrastructure",
    )

    # When
    teardown_organisation_ingestion_infrastructure(organisation_id=organisation.id)

    # Then
    deprovision.assert_called_once_with(organisation.id)
    assert not OrganisationIngestionInfrastructure.objects.filter(
        organisation=organisation
    ).exists()


DELIVERY_BUCKET_NAME = "flagsmith-events-lake-org-1-123456789012-eu-west-2-an"


def _pending_key(environment_key: str, hour: str = "13") -> str:
    return (
        f"events/env_key={environment_key}/year=2026/month=07/day=27/"
        f"hour={hour}/object.gz"
    )


def _delivery_runs_count(result: str) -> float:
    return (
        REGISTRY.get_sample_value(
            "flagsmith_experimentation_warehouse_delivery_runs_total",
            {"result": result},
        )
        or 0.0
    )


def _delivery_objects_count(result: str) -> float:
    return (
        REGISTRY.get_sample_value(
            "flagsmith_experimentation_warehouse_delivery_objects_total",
            {"result": result},
        )
        or 0.0
    )


@pytest.fixture()
def delivery_bucket(aws_credentials: None) -> Iterator[Any]:
    warehouse_delivery_service._get_s3_client.cache_clear()
    with mock_s3():
        s3 = boto3.client("s3", region_name="eu-west-2")
        s3.create_bucket(
            Bucket=DELIVERY_BUCKET_NAME,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
        )
        yield s3
    warehouse_delivery_service._get_s3_client.cache_clear()


@pytest.fixture()
def ingestion_infrastructure(
    organisation: Organisation,
) -> OrganisationIngestionInfrastructure:
    return OrganisationIngestionInfrastructure.objects.create(
        organisation=organisation,
        status=IngestionInfrastructureStatus.CREATED,
        bucket_name=DELIVERY_BUCKET_NAME,
        stream_name="events-ingestion-org-1",
    )


@pytest.fixture()
def warehouse_client(mocker: MockerFixture) -> Any:
    get_client = mocker.patch(
        "experimentation.warehouse_delivery_service.clickhouse_connect.get_client",
    )
    get_client.return_value.raw_insert.return_value.written_rows = 100
    return get_client


def test_deliver_events_to_external_warehouses__mixed_connections__enqueues_clickhouse_only(
    clickhouse_connection: WarehouseConnection,
    project: Project,
    mocker: MockerFixture,
) -> None:
    # Given flagsmith and soft-deleted clickhouse connections alongside the
    # active clickhouse one
    flagsmith_environment = Environment.objects.create(
        name="Flagsmith Warehouse Environment", project=project
    )
    WarehouseConnection.objects.create(
        environment=flagsmith_environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="Flagsmith Warehouse",
    )
    deleted_environment = Environment.objects.create(
        name="Deleted Connection Environment", project=project
    )
    WarehouseConnection.objects.create(
        environment=deleted_environment,
        warehouse_type=WarehouseType.CLICKHOUSE,
        name="Deleted ClickHouse",
    ).delete()
    task = mocker.patch("experimentation.tasks.deliver_events_for_connection")

    # When
    deliver_events_to_external_warehouses()

    # Then
    task.delay.assert_called_once_with(
        kwargs={"connection_id": clickhouse_connection.id},
    )


def test_deliver_events_for_connection__missing_connection__does_nothing(
    db: None,
    warehouse_client: Any,
) -> None:
    # Given no connection with the requested id

    # When
    deliver_events_for_connection(connection_id=404)

    # Then
    warehouse_client.assert_not_called()


def test_deliver_events_for_connection__no_infrastructure__does_nothing(
    clickhouse_connection: WarehouseConnection,
    warehouse_client: Any,
) -> None:
    # Given a connection whose organisation has no ingestion infrastructure

    # When
    deliver_events_for_connection(connection_id=clickhouse_connection.id)

    # Then
    warehouse_client.assert_not_called()


def test_deliver_events_for_connection__infrastructure_without_bucket__does_nothing(
    clickhouse_connection: WarehouseConnection,
    organisation: Organisation,
    warehouse_client: Any,
) -> None:
    # Given
    OrganisationIngestionInfrastructure.objects.create(
        organisation=organisation,
        status=IngestionInfrastructureStatus.PENDING,
    )

    # When
    deliver_events_for_connection(connection_id=clickhouse_connection.id)

    # Then
    warehouse_client.assert_not_called()


def test_deliver_events_for_connection__no_pending_objects__does_not_connect(
    clickhouse_connection: WarehouseConnection,
    ingestion_infrastructure: OrganisationIngestionInfrastructure,
    delivery_bucket: Any,
    warehouse_client: Any,
) -> None:
    # Given an events bucket with no objects for the environment

    # When
    deliver_events_for_connection(connection_id=clickhouse_connection.id)

    # Then
    warehouse_client.assert_not_called()


def test_deliver_events_for_connection__pending_objects__delivers_archives_and_recovers_status(
    clickhouse_connection: WarehouseConnection,
    environment: Environment,
    ingestion_infrastructure: OrganisationIngestionInfrastructure,
    delivery_bucket: Any,
    warehouse_client: Any,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given an errored connection with two objects waiting
    move_object_spy = mocker.spy(warehouse_delivery_service, "move_object")
    clickhouse_connection.status = WarehouseConnectionStatus.ERRORED
    clickhouse_connection.status_detail = "Authentication failed"
    clickhouse_connection.save()
    for hour in ("13", "14"):
        delivery_bucket.put_object(
            Bucket=DELIVERY_BUCKET_NAME,
            Key=_pending_key(environment.api_key, hour=hour),
            Body=b"gzipped-events",
        )
    success_runs_before = _delivery_runs_count("success")
    delivered_objects_before = _delivery_objects_count("delivered")

    # When
    deliver_events_for_connection(connection_id=clickhouse_connection.id)

    # Then both objects are inserted and archived, oldest first
    raw_insert = warehouse_client.return_value.raw_insert
    assert raw_insert.call_count == 2
    assert [call.args[1] for call in move_object_spy.call_args_list] == [
        _pending_key(environment.api_key, hour="13"),
        _pending_key(environment.api_key, hour="14"),
    ]
    archived_keys = [
        item["Key"]
        for item in delivery_bucket.list_objects_v2(
            Bucket=DELIVERY_BUCKET_NAME, Prefix="archive/"
        )["Contents"]
    ]
    assert len(archived_keys) == 2
    assert (
        warehouse_delivery_service.list_pending_objects(
            DELIVERY_BUCKET_NAME,
            environment_key=environment.api_key,
        )
        == []
    )

    # Then each delivery is recorded in the audit ledger
    assert list(
        WarehouseDeliveryLog.objects.filter(connection=clickhouse_connection)
        .order_by("s3_key")
        .values_list("s3_key", "outcome", "rows_count", "error")
    ) == [
        (
            _pending_key(environment.api_key, hour="13"),
            WarehouseDeliveryOutcome.DELIVERED,
            100,
            None,
        ),
        (
            _pending_key(environment.api_key, hour="14"),
            WarehouseDeliveryOutcome.DELIVERED,
            100,
            None,
        ),
    ]

    # Then the delivery success resolves the earlier breakage
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.CONNECTED
    assert clickhouse_connection.status_detail is None

    assert _delivery_runs_count("success") == success_runs_before + 1
    assert _delivery_objects_count("delivered") == delivered_objects_before + 2
    assert {
        "level": "info",
        "event": "delivery.completed",
        "connection__id": clickhouse_connection.id,
        "environment__id": environment.id,
        "organisation__id": environment.project.organisation_id,
        "objects__count": 2,
        "objects__rejected_count": 0,
        "rows__count": 200,
    } in log.events


def test_deliver_events_for_connection__rejected_object__moves_to_failed_and_continues(
    clickhouse_connection: WarehouseConnection,
    environment: Environment,
    ingestion_infrastructure: OrganisationIngestionInfrastructure,
    delivery_bucket: Any,
    warehouse_client: Any,
    log: StructuredLogCapture,
) -> None:
    # Given the warehouse rejects the first object's contents but accepts
    # the second
    clickhouse_connection.status = WarehouseConnectionStatus.CONNECTED
    clickhouse_connection.save()
    for hour in ("13", "14"):
        delivery_bucket.put_object(
            Bucket=DELIVERY_BUCKET_NAME,
            Key=_pending_key(environment.api_key, hour=hour),
            Body=b"gzipped-events",
        )
    raw_insert = warehouse_client.return_value.raw_insert
    raw_insert.side_effect = [
        DatabaseError("Constraint `event_not_empty` violated", code=469),
        raw_insert.return_value,
    ]
    rejected_objects_before = _delivery_objects_count("rejected")

    # When
    deliver_events_for_connection(connection_id=clickhouse_connection.id)

    # Then the rejected object is set aside and the run completes
    failed_keys = [
        item["Key"]
        for item in delivery_bucket.list_objects_v2(
            Bucket=DELIVERY_BUCKET_NAME, Prefix="failed/"
        )["Contents"]
    ]
    assert failed_keys == [
        f"failed/env_key={environment.api_key}/year=2026/month=07/day=27/"
        f"hour=13/object.gz"
    ]
    archived_keys = [
        item["Key"]
        for item in delivery_bucket.list_objects_v2(
            Bucket=DELIVERY_BUCKET_NAME, Prefix="archive/"
        )["Contents"]
    ]
    assert archived_keys == [
        f"archive/env_key={environment.api_key}/year=2026/month=07/day=27/"
        f"hour=14/object.gz"
    ]
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.CONNECTED
    assert _delivery_objects_count("rejected") == rejected_objects_before + 1
    assert log.has("delivery.object_rejected", level="error")

    # Then both outcomes are recorded in the audit ledger, the rejection with
    # its warehouse error
    assert list(
        WarehouseDeliveryLog.objects.filter(connection=clickhouse_connection)
        .order_by("s3_key")
        .values_list("s3_key", "outcome", "rows_count", "error")
    ) == [
        (
            _pending_key(environment.api_key, hour="13"),
            WarehouseDeliveryOutcome.REJECTED,
            None,
            "Constraint `event_not_empty` violated",
        ),
        (
            _pending_key(environment.api_key, hour="14"),
            WarehouseDeliveryOutcome.DELIVERED,
            100,
            None,
        ),
    ]
    assert {
        "level": "info",
        "event": "delivery.completed",
        "connection__id": clickhouse_connection.id,
        "environment__id": environment.id,
        "organisation__id": environment.project.organisation_id,
        "objects__count": 1,
        "objects__rejected_count": 1,
        "rows__count": 100,
    } in log.events


def test_deliver_events_for_connection__warehouse_unusable__aborts_and_marks_errored(
    clickhouse_connection: WarehouseConnection,
    environment: Environment,
    ingestion_infrastructure: OrganisationIngestionInfrastructure,
    delivery_bucket: Any,
    warehouse_client: Any,
    log: StructuredLogCapture,
) -> None:
    # Given the warehouse rejects every request
    for hour in ("13", "14"):
        delivery_bucket.put_object(
            Bucket=DELIVERY_BUCKET_NAME,
            Key=_pending_key(environment.api_key, hour=hour),
            Body=b"gzipped-events",
        )
    warehouse_client.return_value.raw_insert.side_effect = DatabaseError(
        "Authentication failed",
        code=516,
    )
    failure_runs_before = _delivery_runs_count("failure")

    # When
    deliver_events_for_connection(connection_id=clickhouse_connection.id)

    # Then nothing is moved: every object waits for the next run
    assert warehouse_delivery_service.list_pending_objects(
        DELIVERY_BUCKET_NAME,
        environment_key=environment.api_key,
    ) == [
        _pending_key(environment.api_key, hour="13"),
        _pending_key(environment.api_key, hour="14"),
    ]

    # Then the breakage is surfaced on the connection
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.ERRORED
    assert clickhouse_connection.status_detail == "Authentication failed."
    assert _delivery_runs_count("failure") == failure_runs_before + 1
    assert log.has("delivery.failed", level="error")


def test_deliver_events_for_connection__every_object_rejected__marks_errored(
    clickhouse_connection: WarehouseConnection,
    environment: Environment,
    ingestion_infrastructure: OrganisationIngestionInfrastructure,
    delivery_bucket: Any,
    warehouse_client: Any,
    log: StructuredLogCapture,
) -> None:
    # Given a warehouse that rejects the contents of every object, as a table
    # whose schema does not match the payload would
    for hour in ("13", "14"):
        delivery_bucket.put_object(
            Bucket=DELIVERY_BUCKET_NAME,
            Key=_pending_key(environment.api_key, hour=hour),
            Body=b"gzipped-events",
        )
    warehouse_client.return_value.raw_insert.side_effect = DatabaseError(
        "Cannot parse DateTime",
        code=41,
    )
    failure_runs_before = _delivery_runs_count("failure")

    # When
    deliver_events_for_connection(connection_id=clickhouse_connection.id)

    # Then the run is a failure rather than a success, so a schema mismatch is
    # visible instead of draining silently into failed/
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.ERRORED
    assert clickhouse_connection.status_detail == (
        "The warehouse rejected every event object. Check that the `events` "
        "table matches the expected schema."
    )
    assert _delivery_runs_count("failure") == failure_runs_before + 1
    assert log.has("delivery.all_objects_rejected", level="error")


def test_deliver_events_for_connection__time_budget_exhausted__defers_remaining(
    clickhouse_connection: WarehouseConnection,
    environment: Environment,
    ingestion_infrastructure: OrganisationIngestionInfrastructure,
    delivery_bucket: Any,
    warehouse_client: Any,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given three objects waiting and a budget that expires after the first,
    # so the run cannot outlive its task timeout
    for hour in ("13", "14", "15"):
        delivery_bucket.put_object(
            Bucket=DELIVERY_BUCKET_NAME,
            Key=_pending_key(environment.api_key, hour=hour),
            Body=b"gzipped-events",
        )
    # The clock is shared with pytest and Django teardown, so it must keep
    # answering after the budget is spent.
    mocker.patch(
        "experimentation.services.time.monotonic",
        side_effect=itertools.chain([0.0, 0.0], itertools.repeat(1_000.0)),
    )

    # When
    deliver_events_for_connection(connection_id=clickhouse_connection.id)

    # Then only the first object is delivered and the rest wait for the next run
    assert warehouse_client.return_value.raw_insert.call_count == 1
    assert warehouse_delivery_service.list_pending_objects(
        DELIVERY_BUCKET_NAME,
        environment_key=environment.api_key,
    ) == [
        _pending_key(environment.api_key, hour="14"),
        _pending_key(environment.api_key, hour="15"),
    ]
    assert {
        "level": "info",
        "event": "delivery.budget_exhausted",
        "connection__id": clickhouse_connection.id,
        "environment__id": environment.id,
        "organisation__id": environment.project.organisation_id,
        "objects__remaining_count": 2,
    } in log.events
