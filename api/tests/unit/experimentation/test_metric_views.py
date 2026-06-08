from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
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
    # Given

    # When
    response = admin_client_new.post(
        _list_url(environment), data=_numeric_payload(), format="json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_metric__staff_user__returns_403(
    staff_client: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = staff_client.post(
        _list_url(environment), data=_numeric_payload(), format="json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(
    ("aggregation", "event"),
    [
        ("mean", "session_ended"),
        ("occurrence", "activated"),
    ],
)
def test_create_metric__value_free_aggregation__returns_201(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
    aggregation: str,
    event: str,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    payload = {
        "name": "Metric",
        "aggregation": aggregation,
        "definition": {"version": 1, "event": event},
    }

    # When
    response = admin_client_new.post(
        _list_url(environment), data=payload, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "definition",
    [
        pytest.param({"version": 1}, id="missing-event"),
        pytest.param({"event": "session_started"}, id="missing-version"),
        pytest.param(
            {"version": 99, "event": "session_started"}, id="unsupported-version"
        ),
        pytest.param("not-an-object", id="non-object"),
    ],
)
def test_create_metric__invalid_definition__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
    definition: object,
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    payload = {"name": "Bad", "aggregation": "count", "definition": definition}

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
    # Given
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


def test_list_metrics__search_query__filters_by_name(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    _metric(environment, "Checkout Conversion")
    _metric(environment, "Revenue per User")

    # When
    response = admin_client_new.get(_list_url(environment), {"q": "checkout"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    names = [m["name"] for m in response.json()["results"]]
    assert names == ["Checkout Conversion"]


def test_list_metrics__attached_experiments__included(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "with-experiment")
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When
    response = admin_client_new.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["results"][0]
    assert data["experiments"] == [
        {
            "id": experiment.id,
            "name": experiment.name,
            "status": experiment.status,
        }
    ]


@pytest.mark.parametrize(
    "soft_deleted_attachment",
    [
        pytest.param(False, id="unattached"),
        pytest.param(True, id="soft-deleted-attachment"),
    ],
)
def test_list_metrics__no_active_attachment__empty_experiments(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    soft_deleted_attachment: bool,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "no-experiments")
    if soft_deleted_attachment:
        ExperimentMetric.objects.create(
            experiment=experiment,
            metric=metric,
            expected_direction=ExpectedDirection.INCREASE,
        )
        experiment.delete()

    # When
    response = admin_client_new.get(_list_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["experiments"] == []


def test_list_metrics__multiple_attachments__no_n_plus_one(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "first")
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )
    admin_client_new.get(_list_url(environment))
    with CaptureQueriesContext(connection) as one_metric:
        admin_client_new.get(_list_url(environment))

    # When
    for index in range(3):
        extra = _metric(environment, f"extra-{index}")
        ExperimentMetric.objects.create(
            experiment=experiment,
            metric=extra,
            expected_direction=ExpectedDirection.INCREASE,
        )
    with CaptureQueriesContext(connection) as many_metrics:
        admin_client_new.get(_list_url(environment))

    # Then
    assert len(many_metrics) == len(one_metric)


def test_update_metric__patch__updates_and_audits(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "before")

    # When
    no_op_response = admin_client_new.patch(
        _detail_url(environment, metric), data={"name": "before"}, format="json"
    )
    response = admin_client_new.patch(
        _detail_url(environment, metric),
        data={"name": "after", "description": "new desc"},
        format="json",
    )

    # Then
    assert no_op_response.status_code == status.HTTP_200_OK
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "after"
    metric.refresh_from_db()
    assert metric.name == "after"
    assert metric.description == "new desc"
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.METRIC.name,
            related_object_id=metric.id,
            log__contains="updated",
        ).count()
        == 1
    )


def test_update_metric__invalid_definition__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "before")

    # When
    response = admin_client_new.patch(
        _detail_url(environment, metric),
        data={"definition": {"version": 99, "event": "x"}},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "definition" in response.json()


def test_update_metric__staff_user__returns_403(
    staff_client: APIClient,
    environment: Environment,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "before")

    # When
    response = staff_client.patch(
        _detail_url(environment, metric), data={"name": "after"}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


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


@pytest.mark.parametrize(
    "attachment",
    [
        pytest.param("none", id="unattached"),
        pytest.param("completed", id="completed-experiment"),
        pytest.param("soft-deleted", id="soft-deleted-experiment"),
    ],
)
def test_delete_metric__no_active_attachment__returns_204(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    attachment: str,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    metric = _metric(environment, "deletable")
    if attachment == "completed":
        experiment.status = ExperimentStatus.COMPLETED
        experiment.save()
    if attachment in ("completed", "soft-deleted"):
        ExperimentMetric.objects.create(
            experiment=experiment,
            metric=metric,
            expected_direction=ExpectedDirection.INCREASE,
        )
    if attachment == "soft-deleted":
        experiment.delete()

    # When
    response = admin_client_new.delete(_detail_url(environment, metric))

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Metric.objects.filter(name="deletable").exists()


def test_list_metrics__unknown_environment__returns_403(
    admin_client_new: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:experiment_metrics:metrics-list",
        args=["does-not-exist"],
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
