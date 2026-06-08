from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from experimentation.constants import EXPERIMENT_FLAG
from experimentation.models import (
    ExpectedDirection,
    Experiment,
    ExperimentMetric,
    ExperimentStatus,
    Metric,
    MetricAggregation,
    MetricDirection,
)

if TYPE_CHECKING:
    from projects.models import Project
    from tests.types import EnableFeaturesFixture

pytestmark = pytest.mark.django_db


def _list_url(environment: Environment) -> str:
    return reverse(
        "api-v1:environments:experiment_metrics:metrics-list",
        args=[environment.api_key],
    )


def _detail_url(environment: Environment, metric: Metric) -> str:
    return reverse(
        "api-v1:environments:experiment_metrics:metrics-detail",
        args=[environment.api_key, metric.id],
    )


def _numeric_payload(name: str = "Sessions per User") -> dict[str, object]:
    return {
        "name": name,
        "aggregation": "count",
        "definition": {"version": 1, "event": "session_started"},
    }


def _metric(environment: Environment, name: str) -> Metric:
    metric: Metric = Metric.objects.create(
        environment=environment,
        name=name,
        aggregation=MetricAggregation.COUNT,
        definition={"version": 1, "event": "purchase"},
    )
    return metric


def test_create_metric__admin_with_flag__returns_201(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment), data=_numeric_payload(), format="json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Sessions per User"
    metric = Metric.objects.get(id=data["id"])
    assert metric.environment_id == environment.id
    assert AuditLog.objects.filter(
        related_object_type=RelatedObjectType.METRIC.name,
        related_object_id=metric.id,
    ).exists()


def test_create_metric__without_flag__returns_403(
    admin_client_new: APIClient,
    environment: Environment,
) -> None:
    # Given the experiment feature flag is not enabled

    # When an admin tries to create a metric
    response = admin_client_new.post(
        _list_url(environment), data=_numeric_payload(), format="json"
    )

    # Then it is forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_metric__staff_user__returns_403(
    staff_client: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When a non-admin tries to create a metric
    response = staff_client.post(
        _list_url(environment), data=_numeric_payload(), format="json"
    )

    # Then it is forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_metric__mean_without_value__returns_201(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given a mean metric with no explicit value expression
    enable_features(EXPERIMENT_FLAG)
    payload = {
        "name": "Avg Duration",
        "aggregation": "mean",
        "definition": {"version": 1, "event": "session_ended"},
    }

    # When it is created
    response = admin_client_new.post(
        _list_url(environment), data=payload, format="json"
    )

    # Then it is accepted (defaults to the event's value column)
    assert response.status_code == status.HTTP_201_CREATED


def test_create_metric__occurrence_without_value__returns_201(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given — "event happened at least once" needs no value column
    enable_features(EXPERIMENT_FLAG)
    payload = {
        "name": "Activated",
        "aggregation": "occurrence",
        "definition": {"version": 1, "event": "activated"},
    }

    # When
    response = admin_client_new.post(
        _list_url(environment), data=payload, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_create_metric__missing_event__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given a definition with no event
    enable_features(EXPERIMENT_FLAG)
    payload = {
        "name": "Bad",
        "aggregation": "count",
        "definition": {"version": 1},
    }

    # When it is created
    response = admin_client_new.post(
        _list_url(environment), data=payload, format="json"
    )

    # Then it is rejected
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_metric__missing_version__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    payload = {
        "name": "Bad",
        "aggregation": "count",
        "definition": {"event": "session_started"},
    }

    # When
    response = admin_client_new.post(
        _list_url(environment), data=payload, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "definition" in response.json()


def test_create_metric__unsupported_version__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    payload = {
        "name": "Bad",
        "aggregation": "count",
        "definition": {"version": 99, "event": "session_started"},
    }

    # When
    response = admin_client_new.post(
        _list_url(environment), data=payload, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "definition" in response.json()


def test_create_metric__with_direction__persists_direction(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    payload = {
        **_numeric_payload("Time to Activation"),
        "direction": MetricDirection.DOWN,
    }

    # When
    response = admin_client_new.post(
        _list_url(environment), data=payload, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["direction"] == MetricDirection.DOWN
    metric = Metric.objects.get(id=data["id"])
    assert metric.direction == MetricDirection.DOWN


def test_create_metric__without_direction__defaults_to_increase(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment), data=_numeric_payload(), format="json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["direction"] == MetricDirection.UP


def test_list_metrics__other_environment__excluded(
    admin_client_new: APIClient,
    environment: Environment,
    project: "Project",
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given a metric in this environment and one in a sibling environment
    enable_features(EXPERIMENT_FLAG)
    other_env = Environment.objects.create(name="Other", project=project)
    _metric(environment, "mine")
    _metric(other_env, "theirs")

    # When
    response = admin_client_new.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    names = [m["name"] for m in response.json()["results"]]
    assert names == ["mine"]


def test_update_metric__patch__returns_405(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "immutable")

    # When
    response = admin_client_new.patch(
        _detail_url(environment, metric), data={"name": "changed"}, format="json"
    )

    # Then — metrics are immutable for now
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.parametrize(
    "experiment_status",
    [
        ExperimentStatus.CREATED,
        ExperimentStatus.RUNNING,
        ExperimentStatus.PAUSED,
    ],
)
def test_delete_metric__attached_to_active_experiment__returns_409(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    experiment_status: str,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = experiment_status
    experiment.save()
    metric = _metric(environment, "attached")
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When
    response = admin_client_new.delete(_detail_url(environment, metric))

    # Then
    assert response.status_code == status.HTTP_409_CONFLICT
    assert Metric.objects.filter(name="attached").exists()


def test_delete_metric__attached_to_completed_experiment__returns_204(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    experiment.status = ExperimentStatus.COMPLETED
    experiment.save()
    metric = _metric(environment, "done")
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When
    response = admin_client_new.delete(_detail_url(environment, metric))

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Metric.objects.filter(name="done").exists()


def test_delete_metric__attached_to_soft_deleted_experiment__returns_204(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given a metric whose only attachment is to a soft-deleted experiment
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "ghost")
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )
    experiment.delete()  # soft-delete leaves the ExperimentMetric row behind

    # When
    response = admin_client_new.delete(_detail_url(environment, metric))

    # Then the ghost attachment does not block deletion
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_metric__unattached__returns_204(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given a metric not attached to any experiment
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "orphan")

    # When it is deleted
    response = admin_client_new.delete(_detail_url(environment, metric))

    # Then it is removed
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Metric.objects.filter(name="orphan").exists()


def test_create_metric__non_object_definition__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given a definition that is not an object
    enable_features(EXPERIMENT_FLAG)
    payload = {"name": "Bad", "aggregation": "count", "definition": "not-an-object"}

    # When it is created
    response = admin_client_new.post(
        _list_url(environment), data=payload, format="json"
    )

    # Then it is rejected
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "definition" in response.json()


def test_list_metrics__unknown_environment__returns_403(
    admin_client_new: APIClient,
) -> None:
    # Given a non-existent environment api key
    url = reverse(
        "api-v1:environments:experiment_metrics:metrics-list",
        args=["does-not-exist"],
    )

    # When the library is listed
    response = admin_client_new.get(url)

    # Then access is denied
    assert response.status_code == status.HTTP_403_FORBIDDEN
