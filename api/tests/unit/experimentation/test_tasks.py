from dataclasses import asdict
from datetime import datetime
from datetime import timezone as dt_timezone

from django.utils import timezone
from freezegun import freeze_time
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from experimentation.dataclasses import (
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
    MetricResult,
    ResultsSummary,
)
from experimentation.models import (
    Experiment,
    ExperimentExposures,
    ExperimentResults,
    ExperimentStatus,
)
from experimentation.stats import VariantStats
from experimentation.tasks import (
    add_environment_key_to_ingestion,
    compute_experiment_exposures,
    compute_experiment_results,
    delete_environment_key_from_ingestion,
)


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
