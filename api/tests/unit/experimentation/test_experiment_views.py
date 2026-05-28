from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.db import IntegrityError
from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from experimentation.constants import EXPERIMENT_FLAG
from experimentation.models import Experiment, ExperimentStatus
from features.feature_types import MULTIVARIATE
from features.models import Feature
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
