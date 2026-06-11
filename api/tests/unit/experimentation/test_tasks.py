from dataclasses import asdict
from datetime import datetime
from datetime import timezone as dt_timezone

import prometheus_client
from django.utils import timezone
from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from experimentation.dataclasses import (
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
)
from experimentation.models import (
    Experiment,
    ExperimentExposures,
    ExperimentStatus,
)
from experimentation.tasks import (
    add_environment_key_to_ingestion,
    compute_experiment_exposures,
    delete_environment_key_from_ingestion,
    refresh_running_experiment_exposures,
)
from features.models import Feature


def test_add_environment_key_to_ingestion__valid_key__calls_service(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_set = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.set_environment_key",
    )

    # When
    add_environment_key_to_ingestion(environment_api_key="test-env-key-001")

    # Then
    mock_set.assert_called_once_with("test-env-key-001")


def test_delete_environment_key_from_ingestion__valid_key__calls_service(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_delete = mocker.patch(
        "experimentation.tasks.ingestion_sync_service.delete_environment_key",
    )

    # When
    delete_environment_key_from_ingestion(environment_api_key="test-env-key-001")

    # Then
    mock_delete.assert_called_once_with("test-env-key-001")


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


def _computations_count(result: str) -> float:
    return (
        prometheus_client.REGISTRY.get_sample_value(
            "flagsmith_experimentation_exposures_computations_total",
            {"result": result},
        )
        or 0.0
    )


@freeze_time("2026-06-11T12:00:00Z")
def test_compute_experiment_exposures__running_experiment__stores_summary(
    experiment: Experiment,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given a running experiment and a warehouse responding with a summary
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    mock_compute = mocker.patch(
        "experimentation.services.compute_exposures_summary",
        return_value=_summary(),
    )
    success_count = _computations_count("success")

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
    assert _computations_count("success") == success_count + 1
    assert log.events == [
        {
            "level": "info",
            "event": "exposures.computed",
            "experiment__id": experiment.id,
            "environment__id": experiment.environment_id,
            "organisation__id": experiment.environment.project.organisation_id,
            "identities__count": 10,
            "excluded_identities__count": 1,
        }
    ]


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
        "experimentation.services.compute_exposures_summary",
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
        "experimentation.services.compute_exposures_summary",
        side_effect=Exception("warehouse unreachable"),
    )
    failure_count = _computations_count("failure")

    # When
    compute_experiment_exposures(experiment_id=experiment.id)

    # Then the failure is recorded and the last good payload survives
    exposures = ExperimentExposures.objects.get(experiment=experiment)
    assert exposures.last_error_at is not None
    assert exposures.payload == asdict(_summary())
    assert exposures.as_of == as_of
    assert _computations_count("failure") == failure_count + 1
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
        "experimentation.services.compute_exposures_summary",
    )

    # When
    compute_experiment_exposures(experiment_id=experiment.id)

    # Then nothing is queried or stored
    mock_compute.assert_not_called()
    assert not ExperimentExposures.objects.filter(experiment=experiment).exists()


def test_refresh_running_experiment_exposures__running_experiments__enqueues_each(
    experiment: Experiment,
    feature: Feature,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given one running and one created experiment
    settings.EXPERIMENTATION_CLICKHOUSE_URL = "clickhouse://ch.example.com/flagsmith"
    running_experiment = Experiment.objects.create(
        environment=experiment.environment,
        feature=feature,
        name="Running Experiment",
        hypothesis="Hypothesis",
        status=ExperimentStatus.RUNNING,
        started_at=timezone.now(),
    )
    mock_compute = mocker.patch("experimentation.tasks.compute_experiment_exposures")

    # When
    refresh_running_experiment_exposures()

    # Then only the running experiment is enqueued
    mock_compute.delay.assert_called_once_with(
        kwargs={"experiment_id": running_experiment.id},
    )


def test_refresh_running_experiment_exposures__no_warehouse_configured__skips(
    experiment: Experiment,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given a running experiment but no warehouse DSN
    settings.EXPERIMENTATION_CLICKHOUSE_URL = None
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = timezone.now()
    experiment.save()
    mock_compute = mocker.patch("experimentation.tasks.compute_experiment_exposures")

    # When
    refresh_running_experiment_exposures()

    # Then
    mock_compute.delay.assert_not_called()
