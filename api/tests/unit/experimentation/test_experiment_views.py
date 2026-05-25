from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from experimentation.models import Experiment, ExperimentStatus
from features.feature_types import MULTIVARIATE
from features.models import Feature
from tests.types import EnableFeaturesFixture

if TYPE_CHECKING:
    from projects.models import Project

pytestmark = pytest.mark.django_db

EXPERIMENT_FLAG = "experimental_flags"


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


def test_post__valid_multivariate_feature__returns_201(
    admin_client: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.post(
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
    admin_client: APIClient,
    environment: Environment,
    feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.post(
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
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
    organisation_one_project_one: "Project",
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
    response = admin_client.post(
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
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.post(
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
    admin_client: APIClient,
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
    response = admin_client.post(
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


@pytest.mark.parametrize(
    "explicit_status, expected_status_code",
    [
        ("created", 201),
        ("running", 400),
    ],
)
def test_post__explicit_status__returns_expected(
    admin_client: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
    explicit_status: str,
    expected_status_code: int,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "Explicit status",
            "hypothesis": "Testing",
            "status": explicit_status,
        },
        format="json",
    )

    # Then
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "client_fixture, enable_flag, expected_status",
    [
        ("staff_client", True, status.HTTP_403_FORBIDDEN),
        ("admin_client", False, status.HTTP_403_FORBIDDEN),
    ],
)
def test_post__insufficient_permissions__returns_403(
    request: pytest.FixtureRequest,
    environment: Environment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
    client_fixture: str,
    enable_flag: bool,
    expected_status: int,
) -> None:
    # Given
    api_client: APIClient = request.getfixturevalue(client_fixture)
    if enable_flag:
        enable_features(EXPERIMENT_FLAG)

    # When
    response = api_client.post(
        _list_url(environment),
        data={
            "feature": multivariate_feature.id,
            "name": "No access",
            "hypothesis": "Nope",
        },
        format="json",
    )

    # Then
    assert response.status_code == expected_status


def test_post__nonexistent_environment__returns_403(
    admin_client: APIClient,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    url = reverse(
        "api-v1:environments:experiments:experiments-list",
        args=["bad_api_key"],
    )

    # When
    response = admin_client.post(
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
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == experiment.id


def test_get_list__empty__returns_200(
    admin_client: APIClient,
    environment: Environment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


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
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    filter_status: str,
    expected_count: int,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.get(_list_url(environment), {"status": filter_status})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == expected_count


def test_get_detail__exists__returns_200(
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.get(_detail_url(environment, experiment))

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
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    field: str,
    value: str,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.patch(
        _detail_url(environment, experiment),
        data={field: value},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[field] == value


@pytest.mark.parametrize(
    "from_status, to_status, expected_status_code",
    [
        (ExperimentStatus.CREATED, ExperimentStatus.RUNNING, 200),
        (ExperimentStatus.RUNNING, ExperimentStatus.PAUSED, 200),
        (ExperimentStatus.RUNNING, ExperimentStatus.COMPLETED, 200),
        (ExperimentStatus.PAUSED, ExperimentStatus.RUNNING, 200),
        (ExperimentStatus.PAUSED, ExperimentStatus.COMPLETED, 200),
        (ExperimentStatus.CREATED, ExperimentStatus.PAUSED, 400),
        (ExperimentStatus.CREATED, ExperimentStatus.COMPLETED, 400),
        (ExperimentStatus.COMPLETED, ExperimentStatus.RUNNING, 400),
        (ExperimentStatus.COMPLETED, ExperimentStatus.CREATED, 400),
        (ExperimentStatus.RUNNING, ExperimentStatus.CREATED, 400),
    ],
)
def test_patch__status_transition__returns_expected(
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
    from_status: str,
    to_status: str,
    expected_status_code: int,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = from_status
    experiment.save()

    # When
    response = admin_client.patch(
        _detail_url(environment, experiment),
        data={"status": to_status},
        format="json",
    )

    # Then
    assert response.status_code == expected_status_code
    if expected_status_code == 200:
        assert response.json()["status"] == to_status


def test_patch__same_status__returns_200(
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.patch(
        _detail_url(environment, experiment),
        data={"status": "created"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "created"


def test_patch__change_feature__returns_400(
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    project: "Project",
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
    response = admin_client.patch(
        _detail_url(environment, experiment),
        data={"feature": other_feature.id},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_patch__transition_to_running__sets_started_at(
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.patch(
        _detail_url(environment, experiment),
        data={"status": "running"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["started_at"] is not None


def test_patch__transition_to_completed__sets_ended_at(
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.RUNNING
    experiment.save()

    # When
    response = admin_client.patch(
        _detail_url(environment, experiment),
        data={"status": "completed"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["ended_at"] is not None


def test_delete__exists__returns_204_and_soft_deletes(
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client.delete(_detail_url(environment, experiment))

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Experiment.objects.filter(id=experiment.id).exists()
    assert Experiment.objects.all_with_deleted().filter(id=experiment.id).exists()


@pytest.mark.parametrize(
    "method, action_label",
    [
        ("post", "created"),
        ("patch", "updated"),
        ("delete", "deleted"),
    ],
)
def test_crud__any_method__creates_audit_log(
    admin_client: APIClient,
    environment: Environment,
    experiment: Experiment,
    multivariate_feature: Feature,
    enable_features: EnableFeaturesFixture,
    method: str,
    action_label: str,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    if method == "post":
        experiment.delete()
        admin_client.post(
            _list_url(environment),
            data={
                "feature": multivariate_feature.id,
                "name": "Audit test",
                "hypothesis": "Check audit",
            },
            format="json",
        )
    elif method == "patch":
        admin_client.patch(
            _detail_url(environment, experiment),
            data={"name": "Renamed"},
            format="json",
        )
    else:
        admin_client.delete(_detail_url(environment, experiment))

    # Then
    audit = AuditLog.objects.filter(
        related_object_type=RelatedObjectType.EXPERIMENT.name
    ).last()
    assert audit is not None
    assert action_label in audit.log
