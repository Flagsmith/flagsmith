from dataclasses import asdict
from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from django.utils import timezone
from pytest_mock import MockerFixture

from environments.models import Environment
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
    WarehouseConnection,
    WarehouseType,
)
from experimentation.stats import VariantStats


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


def test_experiment_results__record_refresh__stores_payload_and_clears_error(
    experiment: Experiment,
) -> None:
    # Given a row whose last refresh failed
    results = ExperimentResults.objects.create(
        experiment=experiment,
        last_error_at=timezone.now(),
    )
    as_of = timezone.now()

    # When
    results.record_refresh(_results_summary(), as_of)

    # Then the summary is stored as plain JSON and the error marker is cleared
    results.refresh_from_db()
    assert results.payload == {
        "srm_p_value": 0.42,
        "metrics": [
            {
                "metric_id": 7,
                "variants": {
                    "control": {"n": 1000, "sum": 100.0, "sum_squares": 100.0}
                },
                "inference": {},
            }
        ],
    }
    assert results.as_of == as_of
    assert results.last_error_at is None


def test_experiment_results__record_failure__preserves_last_good_payload(
    experiment: Experiment,
) -> None:
    # Given a row holding a previously computed payload
    as_of = timezone.now()
    results = ExperimentResults.objects.create(
        experiment=experiment,
        as_of=as_of,
        payload=asdict(_results_summary()),
    )

    # When
    results.record_failure()

    # Then only the error marker changes
    results.refresh_from_db()
    assert results.last_error_at is not None
    assert results.payload == asdict(_results_summary())
    assert results.as_of == as_of


@pytest.mark.parametrize(
    "ended_at, as_of, expected",
    [
        pytest.param(None, None, False, id="running-uncomputed"),
        pytest.param(
            None,
            datetime(2026, 6, 8, tzinfo=dt_timezone.utc),
            False,
            id="running-computed",
        ),
        pytest.param(
            datetime(2026, 6, 8, tzinfo=dt_timezone.utc),
            datetime(2026, 6, 7, tzinfo=dt_timezone.utc),
            False,
            id="completed-stale",
        ),
        pytest.param(
            datetime(2026, 6, 8, tzinfo=dt_timezone.utc),
            datetime(2026, 6, 8, tzinfo=dt_timezone.utc),
            True,
            id="completed-at-end",
        ),
        pytest.param(
            datetime(2026, 6, 8, tzinfo=dt_timezone.utc),
            datetime(2026, 6, 9, tzinfo=dt_timezone.utc),
            True,
            id="completed-past-end",
        ),
    ],
)
def test_experiment_results__is_final__reflects_window_coverage(
    experiment: Experiment,
    ended_at: datetime | None,
    as_of: datetime | None,
    expected: bool,
) -> None:
    # Given an experiment with a given end and a row computed as of some time
    experiment.ended_at = ended_at

    # When / Then the row is final only once it covers the experiment's end
    results = ExperimentResults(experiment=experiment, as_of=as_of)
    assert results.is_final is expected
