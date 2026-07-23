from dataclasses import asdict
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

import pytest
from django.utils import timezone
from freezegun import freeze_time
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment, EnvironmentAPIKey
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
)
from experimentation.stats import VariantStats
from experimentation.tasks import (
    compute_experiment_exposures,
    compute_experiment_results,
    provision_external_warehouse_ingestion_infrastructure,
    remove_environment_ingestion_key,
    remove_environment_ingestion_keys,
    teardown_organisation_ingestion_infrastructure,
    write_environment_ingestion_key,
    write_environment_ingestion_keys,
)
from organisations.models import Organisation


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
