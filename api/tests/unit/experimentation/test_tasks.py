from dataclasses import asdict
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from typing import Any

import pytest
from django.utils import timezone
from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from task_processor.exceptions import TaskBackoffError

from environments.models import Environment, EnvironmentAPIKey
from experimentation.dataclasses import (
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
    MetricResult,
    ResultsSummary,
    WarehouseDeliveryStatus,
)
from experimentation.models import (
    Experiment,
    ExperimentExposures,
    ExperimentResults,
    ExperimentStatus,
    WarehouseConnection,
    WarehouseConnectionStatus,
)
from experimentation.services import CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS
from experimentation.stats import VariantStats
from experimentation.tasks import (
    apply_warehouse_delivery_statuses,
    compute_experiment_exposures,
    compute_experiment_results,
    remove_environment_ingestion_key,
    sync_environment_ingestion,
    write_environment_ingestion_key,
)


def test_sync_environment_ingestion__flagsmith_connection__whitelists_valid_keys_only(
    warehouse_connection: WarehouseConnection,
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
    mock_service = mocker.Mock()
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.ingestion_sync_service"), "ingestion"
    )
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.warehouse_delivery_sync_service"),
        "delivery",
    )

    # When
    sync_environment_ingestion(environment_id=environment.id)

    # Then the environment follows the default pipeline with no warehouse
    # published, and only the client key and the valid server-side key are
    # whitelisted
    assert mock_service.mock_calls == [
        mocker.call.ingestion.delete_ingestion_destination(environment.api_key),
        mocker.call.delivery.remove_warehouse_connection(environment.api_key),
        mocker.call.ingestion.set_ingestion_key(
            environment.api_key,
            environment_key=environment.api_key,
        ),
        mocker.call.ingestion.set_ingestion_key(
            valid_key.key,
            environment_key=environment.api_key,
            expires_at=valid_key.expires_at,
        ),
    ]


def test_sync_environment_ingestion__external_connection__publishes_then_routes_then_whitelists(
    clickhouse_connection: WarehouseConnection,
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_service = mocker.Mock()
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.ingestion_sync_service"), "ingestion"
    )
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.warehouse_delivery_sync_service"),
        "delivery",
    )

    # When
    sync_environment_ingestion(environment_id=environment.id)

    # Then the connection is in Redis before events are routed to the topic, and
    # the key is whitelisted last, so no event arrives anywhere unplaced
    assert mock_service.mock_calls == [
        mocker.call.delivery.publish_warehouse_connection(
            environment.api_key,
            connection_id=clickhouse_connection.id,
            warehouse_type="clickhouse",
            config=clickhouse_connection.config,
            credentials={"password": "hunter2"},
        ),
        mocker.call.ingestion.set_ingestion_destination(
            environment.api_key,
            topic="external_warehouse_events",
        ),
        mocker.call.ingestion.set_ingestion_key(
            environment.api_key,
            environment_key=environment.api_key,
        ),
    ]


def test_sync_environment_ingestion__connection_deleted__removes_keys_and_destination(
    clickhouse_connection: WarehouseConnection,
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given the environment's only connection is soft-deleted, and it has active
    # and inactive server-side keys
    clickhouse_connection.delete()
    active_key = EnvironmentAPIKey.objects.create(
        environment=environment, name="active"
    )
    inactive_key = EnvironmentAPIKey.objects.create(
        environment=environment, name="inactive", active=False
    )
    mock_service = mocker.Mock()
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.ingestion_sync_service"), "ingestion"
    )
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.warehouse_delivery_sync_service"),
        "delivery",
    )

    # When
    sync_environment_ingestion(environment_id=environment.id)

    # Then the client key and every server-side key are removed regardless of
    # state, and the destination routing is cleared
    assert mock_service.mock_calls == [
        mocker.call.ingestion.delete_ingestion_key(environment.api_key),
        mocker.call.ingestion.delete_ingestion_key(active_key.key),
        mocker.call.ingestion.delete_ingestion_key(inactive_key.key),
        mocker.call.ingestion.delete_ingestion_destination(environment.api_key),
        mocker.call.delivery.remove_warehouse_connection(environment.api_key),
    ]


def test_sync_environment_ingestion__environment_deleted__removes_keys_and_destination(
    clickhouse_connection: WarehouseConnection,
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given the environment is soft-deleted, taking its connection with it
    environment.delete()
    mock_service = mocker.Mock()
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.ingestion_sync_service"), "ingestion"
    )
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.warehouse_delivery_sync_service"),
        "delivery",
    )

    # When
    sync_environment_ingestion(environment_id=environment.id)

    # Then the deleted environment is still found, so its key, destination and
    # connection are removed rather than left accepting events
    assert mock_service.mock_calls == [
        mocker.call.ingestion.delete_ingestion_key(environment.api_key),
        mocker.call.ingestion.delete_ingestion_destination(environment.api_key),
        mocker.call.delivery.remove_warehouse_connection(environment.api_key),
    ]


def test_sync_environment_ingestion__missing_environment__does_nothing(
    db: None,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_service = mocker.Mock()
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.ingestion_sync_service"), "ingestion"
    )
    mock_service.attach_mock(
        mocker.patch("experimentation.tasks.warehouse_delivery_sync_service"),
        "delivery",
    )

    # When
    sync_environment_ingestion(environment_id=404404)

    # Then
    assert mock_service.mock_calls == []


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


def test_compute_experiment_exposures__transient_warehouse_error__records_failure_and_backs_off(
    experiment: Experiment,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    mocker.patch(
        "experimentation.tasks.compute_exposures_summary",
        side_effect=TimeoutError("The read operation timed out"),
    )

    # When
    with pytest.raises(TaskBackoffError):
        compute_experiment_exposures(experiment_id=experiment.id)

    # Then
    exposures = ExperimentExposures.objects.get(experiment=experiment)
    assert exposures.last_error_at is not None
    assert log.has("exposures.compute_failed", level="error")


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
                conversions_timeseries=None,
            )
        ],
        exposures_timeseries=ExposuresTimeseries(granularity="day", points=[]),
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


@pytest.mark.parametrize(
    "exc",
    [
        TimeoutError("The read operation timed out"),
        ConnectionResetError("Connection reset by peer"),
    ],
    ids=["timeout", "reset"],
)
def test_compute_experiment_results__transient_warehouse_error__records_failure_and_backs_off(
    experiment: Experiment,
    mocker: MockerFixture,
    log: StructuredLogCapture,
    exc: Exception,
) -> None:
    # Given
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    mocker.patch(
        "experimentation.tasks.compute_results_summary",
        side_effect=exc,
    )

    # When
    with pytest.raises(TaskBackoffError):
        compute_experiment_results(experiment_id=experiment.id)

    # Then
    results = ExperimentResults.objects.get(experiment=experiment)
    assert results.last_error_at is not None
    assert log.has("results.compute_failed", level="error")


@pytest.mark.parametrize(
    "task_handler",
    [compute_experiment_exposures, compute_experiment_results],
    ids=["exposures", "results"],
)
def test_compute_experiment_task_handlers__task_timeout__exceeds_background_query_timeout(
    task_handler: Any,
) -> None:
    # Given
    task_timeout = task_handler.timeout

    # When / Then
    assert task_timeout is not None
    assert task_timeout.total_seconds() > CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS


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


def test_apply_warehouse_delivery_statuses__errored_outcome__marks_connection_and_logs(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given the delivery service found the customer's warehouse refusing our
    # login, and also left an outcome for a connection that no longer exists
    settings.INGESTION_REDIS_URL = "redis://ingestion:6379"
    mocker.patch(
        "experimentation.tasks.warehouse_delivery_sync_service.pop_warehouse_delivery_statuses",
        return_value=[
            WarehouseDeliveryStatus(
                connection_id=clickhouse_connection.id,
                status="errored",
                detail="Authentication failed.",
            ),
            WarehouseDeliveryStatus(
                connection_id=404404, status="connected", detail=None
            ),
        ],
    )

    # When
    apply_warehouse_delivery_statuses()

    # Then the dashboard shows the failure, and the missing connection is ignored
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.ERRORED
    assert clickhouse_connection.status_detail == "Authentication failed."
    assert log.events == [
        {
            "event": "warehouse_connection.delivery_errored",
            "level": "warning",
            "connection__id": clickhouse_connection.id,
            "status__detail": "Authentication failed.",
        }
    ]


def test_apply_warehouse_delivery_statuses__connected_outcome__clears_detail_quietly(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given a connection the dashboard currently shows as errored, whose
    # warehouse has started taking events again
    settings.INGESTION_REDIS_URL = "redis://ingestion:6379"
    clickhouse_connection.status = WarehouseConnectionStatus.ERRORED
    clickhouse_connection.status_detail = "Could not connect to the host."
    clickhouse_connection.save()
    mocker.patch(
        "experimentation.tasks.warehouse_delivery_sync_service.pop_warehouse_delivery_statuses",
        return_value=[
            WarehouseDeliveryStatus(
                connection_id=clickhouse_connection.id, status="connected", detail=None
            )
        ],
    )

    # When
    apply_warehouse_delivery_statuses()

    # Then the connection recovers, and a routine success is not logged
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.CONNECTED
    assert clickhouse_connection.status_detail is None
    assert log.events == []


def test_apply_warehouse_delivery_statuses__unknown_status__skipped_and_logged(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given a status value the connection model has no choice for
    settings.INGESTION_REDIS_URL = "redis://ingestion:6379"
    mocker.patch(
        "experimentation.tasks.warehouse_delivery_sync_service.pop_warehouse_delivery_statuses",
        return_value=[
            WarehouseDeliveryStatus(
                connection_id=clickhouse_connection.id, status="retrying", detail=None
            )
        ],
    )

    # When
    apply_warehouse_delivery_statuses()

    # Then the connection is left as it was rather than failing the save
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status == WarehouseConnectionStatus.CREATED
    assert log.has(
        "delivery_status.unknown",
        level="warning",
        connection__id=clickhouse_connection.id,
        status="retrying",
    )


def test_apply_warehouse_delivery_statuses__long_detail__cut_to_the_column_length(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given a detail longer than status_detail can hold
    settings.INGESTION_REDIS_URL = "redis://ingestion:6379"
    mocker.patch(
        "experimentation.tasks.warehouse_delivery_sync_service.pop_warehouse_delivery_statuses",
        return_value=[
            WarehouseDeliveryStatus(
                connection_id=clickhouse_connection.id,
                status="errored",
                detail="x" * 300,
            )
        ],
    )

    # When
    apply_warehouse_delivery_statuses()

    # Then
    clickhouse_connection.refresh_from_db()
    assert clickhouse_connection.status_detail == "x" * 255


def test_apply_warehouse_delivery_statuses__ingestion_redis_not_configured__does_nothing(
    db: None,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given a self-hosted installation with no ingestion Redis
    settings.INGESTION_REDIS_URL = ""
    mock_pop = mocker.patch(
        "experimentation.tasks.warehouse_delivery_sync_service.pop_warehouse_delivery_statuses",
    )

    # When
    apply_warehouse_delivery_statuses()

    # Then
    mock_pop.assert_not_called()
