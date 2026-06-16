from dataclasses import asdict

from django.utils import timezone
from pytest_mock import MockerFixture

from environments.models import Environment
from experimentation.dataclasses import (
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
)
from experimentation.models import (
    Experiment,
    ExperimentExposures,
    WarehouseConnection,
    WarehouseType,
)


def test_warehouse_connection__after_create__enqueues_ingestion_add_task(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_task = mocker.patch(
        "experimentation.tasks.add_environment_key_to_ingestion",
    )

    # When
    WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.FLAGSMITH,
        name="warehouse",
    )

    # Then
    mock_task.delay.assert_called_once_with(
        kwargs={"environment_api_key": environment.api_key},
    )


def test_warehouse_connection__after_delete__enqueues_ingestion_delete_task(
    warehouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_task = mocker.patch(
        "experimentation.tasks.delete_environment_key_from_ingestion",
    )
    environment_api_key = warehouse_connection.environment.api_key

    # When
    warehouse_connection.delete()

    # Then
    mock_task.delay.assert_called_once_with(
        kwargs={"environment_api_key": environment_api_key},
    )


def _summary() -> ExposuresSummary:
    return ExposuresSummary(
        excluded_identities=1,
        timeseries=ExposuresTimeseries(
            granularity="hour",
            points=[
                ExposuresTimeseriesPoint(
                    bucket="2026-06-01T00:00:00+00:00",
                    new_identities={"control": 10},
                )
            ],
        ),
    )


def test_experiment_exposures__record_refresh__stores_payload_and_clears_error(
    experiment: Experiment,
) -> None:
    # Given a row whose last refresh failed
    exposures = ExperimentExposures.objects.create(
        experiment=experiment,
        last_error_at=timezone.now(),
    )
    as_of = timezone.now()

    # When
    exposures.record_refresh(_summary(), as_of)

    # Then the summary is stored as plain JSON and the error marker is cleared
    exposures.refresh_from_db()
    assert exposures.payload == {
        "excluded_identities": 1,
        "timeseries": {
            "granularity": "hour",
            "points": [
                {
                    "bucket": "2026-06-01T00:00:00+00:00",
                    "new_identities": {"control": 10},
                }
            ],
        },
    }
    assert exposures.as_of == as_of
    assert exposures.last_error_at is None


def test_experiment_exposures__record_failure__preserves_last_good_payload(
    experiment: Experiment,
) -> None:
    # Given a row holding a previously computed payload
    as_of = timezone.now()
    exposures = ExperimentExposures.objects.create(
        experiment=experiment,
        as_of=as_of,
        payload=asdict(_summary()),
    )

    # When
    exposures.record_failure()

    # Then only the error marker changes
    exposures.refresh_from_db()
    assert exposures.last_error_at is not None
    assert exposures.payload == asdict(_summary())
    assert exposures.as_of == as_of
