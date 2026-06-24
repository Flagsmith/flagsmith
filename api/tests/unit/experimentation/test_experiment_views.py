from __future__ import annotations

from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from typing import TYPE_CHECKING

import pytest
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from experimentation.constants import (
    EXPERIMENT_FLAG,
    EXPOSURES_REFRESH_MIN_INTERVAL,
    RESULTS_REFRESH_MIN_INTERVAL,
)
from experimentation.models import (
    ExpectedDirection,
    Experiment,
    ExperimentExposures,
    ExperimentMetric,
    ExperimentResults,
    ExperimentStatus,
    Metric,
)
from experimentation.serializers import ExperimentFeatureSerializer
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from segments.models import Condition
from tests.types import EnableFeaturesFixture

if TYPE_CHECKING:
    from projects.models import Project

pytestmark = pytest.mark.django_db


def _list_url(environment: Environment) -> str:
    return reverse(
        "api-v1:environments:experiments:experiments-list",
        args=[environment.api_key],
    )


def _detail_url(environment: Environment, experiment: Experiment) -> str:
    return reverse(
        "api-v1:environments:experiments:experiments-detail",
        args=[environment.api_key, experiment.id],
    )


def _action_url(environment: Environment, experiment: Experiment, action: str) -> str:
    return reverse(
        f"api-v1:environments:experiments:experiments-{action}",
        args=[environment.api_key, experiment.id],
    )


def test_post__valid_multivariate_feature__returns_201(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "My experiment",
            "hypothesis": "It will work",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["feature"] == multivariate_feature.id
    assert data["name"] == "My experiment"
    assert data["status"] == "created"
    assert data["started_at"] is None
    assert data["ended_at"] is None


def test_post__non_multivariate_feature__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": feature.id,
            "name": "Bad experiment",
            "hypothesis": "Nope",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_post__feature_from_different_project__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    organisation_one_project_one: Project,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    other_feature = Feature.objects.create(
        project=organisation_one_project_one,
        name="other_mv_feature",
        type=MULTIVARIATE,
        initial_value="control",
    )

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": other_feature.id,
            "name": "Wrong project",
            "hypothesis": "Nope",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_post__active_experiment_exists__returns_409(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Duplicate",
            "hypothesis": "Should fail",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_409_CONFLICT


def test_post__completed_experiment_exists__returns_201(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.COMPLETED
    experiment.save()

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "New experiment",
            "hypothesis": "Should work",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_post__staff_user_with_flag__returns_403(
    staff_client: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = staff_client.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "No access",
            "hypothesis": "Nope",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_post__admin_without_flag__returns_403(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
) -> None:
    # Given — feature flag not enabled

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "No access",
            "hypothesis": "Nope",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_post__nonexistent_environment__returns_403(
    admin_client_new: APIClient,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    url = reverse(
        "api-v1:environments:experiments:experiments-list",
        args=["bad_api_key"],
    )

    # When
    response = admin_client_new.post(
        url,
        data={
            "feature": 999,
            "name": "Bad env",
            "hypothesis": "Nope",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_list__with_experiments__returns_all(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == experiment.id


def test_get_list__with_experiments__returns_nested_feature(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    feature_data = results[0]["feature"]
    assert isinstance(feature_data, dict)
    assert feature_data["id"] == multivariate_feature.id
    assert feature_data["name"] == multivariate_feature.name
    assert feature_data["type"] == "MULTIVARIATE"
    assert feature_data["initial_value"] == "control"
    assert len(feature_data["multivariate_options"]) == 3


def test_get_detail__exists__returns_nested_feature(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_detail_url(environment, experiment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    feature_data = response.json()["feature"]
    assert isinstance(feature_data, dict)
    assert feature_data["id"] == multivariate_feature.id
    assert feature_data["name"] == multivariate_feature.name


def test_get_list__empty__returns_200(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


@pytest.mark.parametrize(
    "filter_status, expected_count",
    [
        ("created", 1),
        ("running", 0),
        ("paused", 0),
        ("completed", 0),
    ],
)
def test_get_list__filter_by_status__returns_filtered(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    filter_status: str,
    expected_count: int,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_list_url(environment), {"status": filter_status})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == expected_count


def test_get_list__search_by_experiment_name__returns_matching(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_list_url(environment), {"q": experiment.name[:4]})

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == experiment.id


def test_get_list__search_by_feature_name__returns_matching(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(
        _list_url(environment), {"q": multivariate_feature.name}
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id"] == experiment.id


def test_get_list__search_no_match__returns_empty(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_list_url(environment), {"q": "nonexistent"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 0


def test_get_list__with_experiments__returns_status_counts(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
    project: Project,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    second_feature = Feature.objects.create(
        project=project,
        name="second_mv_feature",
        type=MULTIVARIATE,
        initial_value="control",
    )
    running_experiment = Experiment.objects.create(
        environment=environment,
        feature=second_feature,
        name="Running experiment",
        hypothesis="Test",
        status=ExperimentStatus.RUNNING,
    )

    # When
    response = admin_client_new.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status_counts"] == {
        "created": 1,
        "running": 1,
        "paused": 0,
        "completed": 0,
    }
    assert len(data["results"]) == 2

    # Clean up
    running_experiment.delete()


def test_get_list__filtered__status_counts_reflect_all(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_list_url(environment), {"status": "running"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 0
    assert data["status_counts"]["created"] == 1
    assert data["status_counts"]["running"] == 0


def test_get_list__searched__status_counts_reflect_search(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_list_url(environment), {"q": "nonexistent"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["results"]) == 0
    assert data["status_counts"]["created"] == 0
    assert data["status_counts"]["running"] == 0


def test_get_detail__exists__returns_200(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_detail_url(environment, experiment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == experiment.id


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", "Updated name"),
        ("hypothesis", "Updated hypothesis"),
    ],
)
def test_patch__update_field__returns_200(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    field: str,
    value: str,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.patch(
        _detail_url(environment, experiment),
        data={field: value},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[field] == value


def test_patch__change_feature__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    project: Project,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    other_feature = Feature.objects.create(
        project=project,
        name="other_mv_feature",
        type=MULTIVARIATE,
        initial_value="control",
    )

    # When
    response = admin_client_new.patch(
        _detail_url(environment, experiment),
        data={"feature": other_feature.id},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "from_status, action_name, expected_status_code",
    [
        (ExperimentStatus.CREATED, "start", 200),
        (ExperimentStatus.RUNNING, "pause", 200),
        (ExperimentStatus.RUNNING, "complete", 200),
        (ExperimentStatus.PAUSED, "start", 200),
        (ExperimentStatus.PAUSED, "complete", 200),
        (ExperimentStatus.CREATED, "pause", 400),
        (ExperimentStatus.CREATED, "complete", 400),
        (ExperimentStatus.COMPLETED, "start", 400),
        (ExperimentStatus.COMPLETED, "pause", 400),
        (ExperimentStatus.RUNNING, "start", 400),
    ],
)
def test_action__status_transition__returns_expected(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    from_status: str,
    action_name: str,
    expected_status_code: int,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = from_status
    experiment.save()

    # When
    response = admin_client_new.post(_action_url(environment, experiment, action_name))

    # Then
    assert response.status_code == expected_status_code


def test_action__start__sets_started_at(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(_action_url(environment, experiment, "start"))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["started_at"] is not None


def test_action__complete__sets_ended_at(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.RUNNING
    experiment.save()

    # When
    response = admin_client_new.post(_action_url(environment, experiment, "complete"))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["ended_at"] is not None


def test_exposures__computed_row__returns_row(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a previously computed exposures row
    enable_features(EXPERIMENT_FLAG)
    payload = {
        "excluded_identities": 4,
        "timeseries": {
            "granularity": "day",
            "points": [
                {
                    "bucket": "2026-06-01T00:00:00+00:00",
                    "new_identities": {"control": 310, "variant_a": 295},
                }
            ],
        },
    }
    ExperimentExposures.objects.create(
        experiment=experiment,
        as_of=datetime(2026, 6, 11, 12, tzinfo=dt_timezone.utc),
        payload=payload,
    )

    # When
    response = admin_client_new.get(_action_url(environment, experiment, "exposures"))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "exposures": {
            "as_of": "2026-06-11T12:00:00Z",
            "last_error_at": None,
            "refresh_requested_at": None,
            "payload": payload,
            "is_final": False,
        }
    }


def test_exposures__never_computed__returns_null(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_action_url(environment, experiment, "exposures"))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"exposures": None}


def test_exposures__failed_refresh__returns_error_marker_with_last_payload(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a row whose last refresh failed after an earlier success
    enable_features(EXPERIMENT_FLAG)
    payload = {
        "excluded_identities": 0,
        "timeseries": {"granularity": "hour", "points": []},
    }
    ExperimentExposures.objects.create(
        experiment=experiment,
        as_of=datetime(2026, 6, 11, 11, tzinfo=dt_timezone.utc),
        payload=payload,
        last_error_at=datetime(2026, 6, 11, 12, tzinfo=dt_timezone.utc),
    )

    # When
    response = admin_client_new.get(_action_url(environment, experiment, "exposures"))

    # Then the stale data and the error marker are both surfaced
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "exposures": {
            "as_of": "2026-06-11T11:00:00Z",
            "last_error_at": "2026-06-11T12:00:00Z",
            "refresh_requested_at": None,
            "payload": payload,
            "is_final": False,
        }
    }


def test_exposures__admin_without_flag__returns_403(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
) -> None:
    # Given — feature flag not enabled

    # When
    response = admin_client_new.get(_action_url(environment, experiment, "exposures"))

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_exposures__staff_user_with_flag__returns_403(
    staff_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = staff_client.get(_action_url(environment, experiment, "exposures"))

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_refresh_exposures__started_experiment__enqueues_compute(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    mock_compute = mocker.patch("experimentation.views.compute_experiment_exposures")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-exposures")
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_compute.delay.assert_called_once_with(
        kwargs={"experiment_id": experiment.id},
    )
    exposures = ExperimentExposures.objects.get(experiment=experiment)
    assert exposures.refresh_requested_at is not None


@freeze_time("2026-06-11T12:00:00Z")
def test_refresh_exposures__requested_recently__returns_429_with_retry_after(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given a refresh was requested a minute ago
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentExposures.objects.create(
        experiment=experiment,
        refresh_requested_at=timezone.now() - timedelta(minutes=1),
    )
    mock_compute = mocker.patch("experimentation.views.compute_experiment_exposures")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-exposures")
    )

    # Then the client is told when to retry
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.headers["Retry-After"] == "240"
    mock_compute.delay.assert_not_called()


def test_refresh_exposures__last_request_beyond_interval__enqueues_compute(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given the last refresh request is older than the minimum interval
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentExposures.objects.create(
        experiment=experiment,
        refresh_requested_at=timezone.now() - EXPOSURES_REFRESH_MIN_INTERVAL,
    )
    mock_compute = mocker.patch("experimentation.views.compute_experiment_exposures")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-exposures")
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_compute.delay.assert_called_once()


def test_refresh_exposures__completed_with_final_row__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given a completed experiment whose row already covers the full window
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.COMPLETED
    experiment.started_at = datetime(2026, 6, 1, tzinfo=dt_timezone.utc)
    experiment.ended_at = datetime(2026, 6, 8, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentExposures.objects.create(
        experiment=experiment,
        as_of=experiment.ended_at,
        payload={"excluded_identities": 0},
    )
    mock_compute = mocker.patch("experimentation.views.compute_experiment_exposures")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-exposures")
    )

    # Then the final data cannot be recomputed away (events expire in the
    # warehouse after 90 days)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_compute.delay.assert_not_called()


def test_refresh_exposures__completed_with_stale_row__enqueues_compute(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given a completed experiment last computed before it ended
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.COMPLETED
    experiment.started_at = datetime(2026, 6, 1, tzinfo=dt_timezone.utc)
    experiment.ended_at = datetime(2026, 6, 8, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentExposures.objects.create(
        experiment=experiment,
        as_of=datetime(2026, 6, 7, tzinfo=dt_timezone.utc),
        payload={"excluded_identities": 0},
    )
    mock_compute = mocker.patch("experimentation.views.compute_experiment_exposures")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-exposures")
    )

    # Then the finalising refresh is allowed
    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_compute.delay.assert_called_once()


def test_refresh_exposures__not_started_experiment__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given a created experiment that has never started
    enable_features(EXPERIMENT_FLAG)
    mock_compute = mocker.patch("experimentation.views.compute_experiment_exposures")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-exposures")
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_compute.delay.assert_not_called()


def test_refresh_exposures__staff_user_with_flag__returns_403(
    staff_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = staff_client.post(
        _action_url(environment, experiment, "refresh-exposures")
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete__exists__returns_204_and_soft_deletes(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.delete(_detail_url(environment, experiment))

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Experiment.objects.filter(id=experiment.id).exists()
    assert Experiment.objects.all_with_deleted().filter(id=experiment.id).exists()


def test_post__valid_create__creates_audit_log(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Audit test",
            "hypothesis": "Check audit",
        },
        format="json",
    )

    # Then
    audit = AuditLog.objects.filter(
        related_object_type=RelatedObjectType.EXPERIMENT.name
    ).last()
    assert audit is not None
    assert "created" in audit.log


def test_patch__valid_update__creates_audit_log(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    admin_client_new.patch(
        _detail_url(environment, experiment),
        data={"name": "Renamed"},
        format="json",
    )

    # Then
    audit = AuditLog.objects.filter(
        related_object_type=RelatedObjectType.EXPERIMENT.name
    ).last()
    assert audit is not None
    assert "updated" in audit.log


def test_action__start__creates_audit_log(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    admin_client_new.post(_action_url(environment, experiment, "start"))

    # Then
    audit = AuditLog.objects.filter(
        related_object_type=RelatedObjectType.EXPERIMENT.name
    ).last()
    assert audit is not None
    assert "running" in audit.log


def test_delete__valid_delete__creates_audit_log(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    admin_client_new.delete(_detail_url(environment, experiment))

    # Then
    audit = AuditLog.objects.filter(
        related_object_type=RelatedObjectType.EXPERIMENT.name
    ).last()
    assert audit is not None
    assert "deleted" in audit.log


def test_get_list__invalid_status__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_list_url(environment), {"status": "garbage"})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete__running_experiment__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.RUNNING
    experiment.save()

    # When
    response = admin_client_new.delete(_detail_url(environment, experiment))

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Experiment.objects.filter(id=experiment.id).exists()


def test_patch__no_change__skips_audit_log(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    audit_count_before = AuditLog.objects.filter(
        related_object_type=RelatedObjectType.EXPERIMENT.name
    ).count()

    # When
    response = admin_client_new.patch(
        _detail_url(environment, experiment),
        data={"name": experiment.name},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    audit_count_after = AuditLog.objects.filter(
        related_object_type=RelatedObjectType.EXPERIMENT.name
    ).count()
    assert audit_count_after == audit_count_before


def test_post__inline_metric__creates_experiment_metric(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    metric: Metric,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "With metric",
            "hypothesis": "It will work",
            "metrics": [
                {"metric": metric.id, "expected_direction": "increase"},
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    experiment_metric = ExperimentMetric.objects.get(
        experiment_id=response.json()["id"]
    )
    assert experiment_metric.metric == metric
    assert experiment_metric.expected_direction == ExpectedDirection.INCREASE


def test_post__metric_from_other_environment__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
    project: Project,
) -> None:
    # Given a metric defined in a sibling environment
    enable_features(EXPERIMENT_FLAG)
    other_env = Environment.objects.create(name="Other", project=project)
    foreign = Metric.objects.create(
        environment=other_env,
        name="foreign",
        definition={"version": 1, "event": "x"},
    )

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Foreign metric",
            "hypothesis": "Should fail",
            "metrics": [
                {"metric": foreign.id, "expected_direction": "increase"},
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Experiment.objects.filter(name="Foreign metric").exists()


def test_post__duplicate_metrics__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    metric: Metric,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Duplicate metrics",
            "hypothesis": "Should fail",
            "metrics": [
                {"metric": metric.id, "expected_direction": "increase"},
                {"metric": metric.id, "expected_direction": "decrease"},
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not Experiment.objects.filter(name="Duplicate metrics").exists()


def test_post__invalid_expected_direction__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    metric: Metric,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Bad direction",
            "hypothesis": "Should fail",
            "metrics": [
                {"metric": metric.id, "expected_direction": "sideways"},
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_patch__metrics__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    metric: Metric,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.patch(
        _detail_url(environment, experiment),
        data={
            "metrics": [
                {"metric": metric.id, "expected_direction": "increase"},
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not experiment.experiment_metrics.exists()


def test_get_list__with_attached_metric__returns_metrics(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    metric: Metric,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When
    response = admin_client_new.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    metrics_data = response.json()["results"][0]["metrics"]
    assert len(metrics_data) == 1
    assert metrics_data[0]["metric"] == metric.id
    assert metrics_data[0]["metric_name"] == metric.name
    assert metrics_data[0]["expected_direction"] == "increase"


def test_get_detail__with_attached_metric__returns_metrics(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    metric: Metric,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When
    response = admin_client_new.get(_detail_url(environment, experiment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    metrics_data = response.json()["metrics"]
    assert len(metrics_data) == 1
    assert metrics_data[0]["metric"] == metric.id


def test_post__concurrent_create_race__returns_409(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    mocker.patch(
        "experimentation.views.ExperimentViewSet.perform_create",
        side_effect=IntegrityError(),
    )

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Race",
            "hypothesis": "Should 409",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_409_CONFLICT


def test_results__computed_row__returns_row(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a previously computed results row
    enable_features(EXPERIMENT_FLAG)
    payload = {
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
    ExperimentResults.objects.create(
        experiment=experiment,
        as_of=datetime(2026, 6, 11, 12, tzinfo=dt_timezone.utc),
        payload=payload,
    )

    # When
    response = admin_client_new.get(_action_url(environment, experiment, "results"))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": {
            "as_of": "2026-06-11T12:00:00Z",
            "last_error_at": None,
            "refresh_requested_at": None,
            "payload": payload,
            "is_final": False,
        }
    }


def test_results__never_computed__returns_null(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_action_url(environment, experiment, "results"))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"results": None}


def test_results__failed_refresh__returns_error_marker_with_last_payload(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given a row whose last refresh failed after an earlier success
    enable_features(EXPERIMENT_FLAG)
    payload: dict[str, object] = {"srm_p_value": None, "metrics": []}
    ExperimentResults.objects.create(
        experiment=experiment,
        as_of=datetime(2026, 6, 11, 11, tzinfo=dt_timezone.utc),
        payload=payload,
        last_error_at=datetime(2026, 6, 11, 12, tzinfo=dt_timezone.utc),
    )

    # When
    response = admin_client_new.get(_action_url(environment, experiment, "results"))

    # Then the stale data and the error marker are both surfaced
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": {
            "as_of": "2026-06-11T11:00:00Z",
            "last_error_at": "2026-06-11T12:00:00Z",
            "refresh_requested_at": None,
            "payload": payload,
            "is_final": False,
        }
    }


def test_results__admin_without_flag__returns_403(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
) -> None:
    # Given — feature flag not enabled

    # When
    response = admin_client_new.get(_action_url(environment, experiment, "results"))

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_results__staff_user_with_flag__returns_403(
    staff_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = staff_client.get(_action_url(environment, experiment, "results"))

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_refresh_results__started_experiment__enqueues_compute(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    mock_compute = mocker.patch("experimentation.views.compute_experiment_results")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-results")
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_compute.delay.assert_called_once_with(
        kwargs={"experiment_id": experiment.id},
    )
    results = ExperimentResults.objects.get(experiment=experiment)
    assert results.refresh_requested_at is not None


@freeze_time("2026-06-11T12:00:00Z")
def test_refresh_results__requested_recently__returns_429_with_retry_after(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given a refresh was requested a minute ago
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentResults.objects.create(
        experiment=experiment,
        refresh_requested_at=timezone.now() - timedelta(minutes=1),
    )
    mock_compute = mocker.patch("experimentation.views.compute_experiment_results")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-results")
    )

    # Then the client is told when to retry
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.headers["Retry-After"] == "240"
    mock_compute.delay.assert_not_called()


def test_refresh_results__last_request_beyond_interval__enqueues_compute(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given the last refresh request is older than the minimum interval
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.RUNNING
    experiment.started_at = datetime(2026, 6, 10, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentResults.objects.create(
        experiment=experiment,
        refresh_requested_at=timezone.now() - RESULTS_REFRESH_MIN_INTERVAL,
    )
    mock_compute = mocker.patch("experimentation.views.compute_experiment_results")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-results")
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_compute.delay.assert_called_once()


def test_refresh_results__completed_with_final_row__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given a completed experiment whose row already covers the full window
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.COMPLETED
    experiment.started_at = datetime(2026, 6, 1, tzinfo=dt_timezone.utc)
    experiment.ended_at = datetime(2026, 6, 8, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentResults.objects.create(
        experiment=experiment,
        as_of=experiment.ended_at,
        payload={"srm_p_value": None, "metrics": []},
    )
    mock_compute = mocker.patch("experimentation.views.compute_experiment_results")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-results")
    )

    # Then a final row is not recomputed
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_compute.delay.assert_not_called()


def test_refresh_results__completed_with_stale_row__enqueues_compute(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given a completed experiment last computed before it ended
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.COMPLETED
    experiment.started_at = datetime(2026, 6, 1, tzinfo=dt_timezone.utc)
    experiment.ended_at = datetime(2026, 6, 8, tzinfo=dt_timezone.utc)
    experiment.save()
    ExperimentResults.objects.create(
        experiment=experiment,
        as_of=datetime(2026, 6, 7, tzinfo=dt_timezone.utc),
        payload={"srm_p_value": None, "metrics": []},
    )
    mock_compute = mocker.patch("experimentation.views.compute_experiment_results")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-results")
    )

    # Then the finalising refresh is allowed
    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_compute.delay.assert_called_once()


def test_refresh_results__not_started_experiment__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    mocker: MockerFixture,
) -> None:
    # Given a created experiment that has never started
    enable_features(EXPERIMENT_FLAG)
    mock_compute = mocker.patch("experimentation.views.compute_experiment_results")

    # When
    response = admin_client_new.post(
        _action_url(environment, experiment, "refresh-results")
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_compute.delay.assert_not_called()


def test_refresh_results__staff_user_with_flag__returns_403(
    staff_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = staff_client.post(
        _action_url(environment, experiment, "refresh-results")
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_detail__env_level_allocations__returns_environment_percentages(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    env_fs = FeatureState.objects.get(
        feature=multivariate_feature,
        environment=environment,
        identity__isnull=True,
        feature_segment__isnull=True,
    )
    env_allocations = [10.0, 20.0, 70.0]
    for mv_fsv, alloc in zip(
        MultivariateFeatureStateValue.objects.filter(feature_state=env_fs).order_by(
            "multivariate_feature_option_id"
        ),
        env_allocations,
    ):
        mv_fsv.percentage_allocation = alloc
        mv_fsv.save()

    # When
    response = admin_client_new.get(_detail_url(environment, experiment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    options = response.json()["feature"]["multivariate_options"]
    returned_allocs = sorted(o["default_percentage_allocation"] for o in options)
    assert returned_allocs == sorted(env_allocations)


def test_experiment_feature_serializer__no_environment_context__raises(
    multivariate_feature: Feature,
) -> None:
    # Given
    serializer = ExperimentFeatureSerializer(multivariate_feature, context={})

    # When / Then
    with pytest.raises(ValueError, match="requires 'environment' in context"):
        serializer.data


def test_experiment_feature_serializer__no_env_feature_state__raises(
    environment: Environment,
    multivariate_feature: Feature,
) -> None:
    # Given
    FeatureState.objects.filter(
        feature=multivariate_feature,
        environment=environment,
        identity__isnull=True,
        feature_segment__isnull=True,
    ).delete()
    serializer = ExperimentFeatureSerializer(
        multivariate_feature, context={"environment": environment}
    )

    # When / Then
    with pytest.raises(ValueError, match="No environment feature state found"):
        serializer.data


def test_post__with_experiment_rollout__creates_rollout(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    option_a, option_b, _ = multivariate_options

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Rollout experiment",
            "hypothesis": "It will work",
            "experiment_rollout": {
                "enabled": True,
                "rollout_percentage": 30,
                "feature_state_value": {"type": "string", "value": "control"},
                "multivariate_feature_state_values": [
                    {
                        "multivariate_feature_option": option_a.id,
                        "percentage_allocation": 60,
                    },
                    {
                        "multivariate_feature_option": option_b.id,
                        "percentage_allocation": 40,
                    },
                ],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    experiment = Experiment.objects.get(id=response.json()["id"])
    assert experiment.rollout_segment is not None
    assert experiment.rollout_segment.is_system_segment is True


def test_post__rollout_allocations_exceed_100__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    option_a, option_b, _ = multivariate_options

    # When the allocations sum to more than 100%
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Rollout experiment",
            "hypothesis": "It will work",
            "experiment_rollout": {
                "enabled": True,
                "rollout_percentage": 30,
                "feature_state_value": {"type": "string", "value": "control"},
                "multivariate_feature_state_values": [
                    {
                        "multivariate_feature_option": option_a.id,
                        "percentage_allocation": 60,
                    },
                    {
                        "multivariate_feature_option": option_b.id,
                        "percentage_allocation": 60,
                    },
                ],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "exceed" in str(response.json()).lower()


def test_post__rollout_mv_option_not_on_feature__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Rollout experiment",
            "hypothesis": "It will work",
            "experiment_rollout": {
                "enabled": True,
                "rollout_percentage": 30,
                "feature_state_value": {"type": "string", "value": "control"},
                "multivariate_feature_state_values": [
                    {
                        "multivariate_feature_option": 999999,
                        "percentage_allocation": 100,
                    },
                ],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "do not belong to the feature" in str(response.json())


def test_action_rollout__valid__updates_percentage(
    admin_client_new: APIClient,
    environment: Environment,
    experiment_with_rollout: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    option_a, option_b, _ = multivariate_options

    # When
    response = admin_client_new.patch(
        _action_url(environment, experiment_with_rollout, "rollout"),
        data={
            "enabled": False,
            "rollout_percentage": 75,
            "feature_state_value": {"type": "string", "value": "control"},
            "multivariate_feature_state_values": [
                {
                    "multivariate_feature_option": option_a.id,
                    "percentage_allocation": 50,
                },
                {
                    "multivariate_feature_option": option_b.id,
                    "percentage_allocation": 50,
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    condition = Condition.objects.get(
        rule__segment=experiment_with_rollout.rollout_segment
    )
    assert condition.value == "75.0"


def test_action_rollout__running_experiment__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment_with_rollout: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment_with_rollout.status = ExperimentStatus.RUNNING
    experiment_with_rollout.save()
    option_a, option_b, _ = multivariate_options

    # When
    response = admin_client_new.patch(
        _action_url(environment, experiment_with_rollout, "rollout"),
        data={
            "enabled": True,
            "rollout_percentage": 75,
            "feature_state_value": {"type": "string", "value": "control"},
            "multivariate_feature_state_values": [
                {
                    "multivariate_feature_option": option_a.id,
                    "percentage_allocation": 50,
                },
                {
                    "multivariate_feature_option": option_b.id,
                    "percentage_allocation": 50,
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_action_rollout__mv_option_not_on_feature__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment_with_rollout: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.patch(
        _action_url(environment, experiment_with_rollout, "rollout"),
        data={
            "enabled": True,
            "rollout_percentage": 75,
            "feature_state_value": {"type": "string", "value": "control"},
            "multivariate_feature_state_values": [
                {
                    "multivariate_feature_option": 999999,
                    "percentage_allocation": 100,
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "do not belong to the feature" in str(response.json())


def test_patch__experiment_rollout_on_update__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.patch(
        _detail_url(environment, experiment),
        data={
            "experiment_rollout": {
                "enabled": True,
                "rollout_percentage": 30,
                "feature_state_value": {"type": "string", "value": "control"},
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot change the rollout" in str(response.json())


def test_get_detail__with_rollout__returns_rollout(
    admin_client_new: APIClient,
    environment: Environment,
    experiment_with_rollout: Experiment,
    multivariate_options: list[MultivariateFeatureOption],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    option_a, option_b, _ = multivariate_options

    # When
    response = admin_client_new.get(_detail_url(environment, experiment_with_rollout))

    # Then
    assert response.status_code == status.HTTP_200_OK
    rollout = response.json()["experiment_rollout"]
    assert rollout["enabled"] is True
    assert rollout["rollout_percentage"] == 20.0
    assert rollout["feature_state_value"] == {"type": "string", "value": "control"}
    assert {
        (mv["multivariate_feature_option"], mv["percentage_allocation"])
        for mv in rollout["multivariate_feature_state_values"]
    } == {(option_a.id, 50.0), (option_b.id, 50.0)}


def test_get_detail__without_rollout__returns_null(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.get(_detail_url(environment, experiment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["experiment_rollout"] is None
