from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from experimentation.constants import EXPERIMENT_FLAG
from experimentation.models import (
    ExpectedDirection,
    Experiment,
    ExperimentMetric,
    Metric,
)

if TYPE_CHECKING:
    from projects.models import Project
    from tests.types import EnableFeaturesFixture

pytestmark = pytest.mark.django_db


def _list_url(environment: Environment, experiment: Experiment) -> str:
    return reverse(
        "api-v1:environments:experiments:experiment-metrics-list",
        args=[environment.api_key, experiment.id],
    )


def _detail_url(
    environment: Environment, experiment: Experiment, em: ExperimentMetric
) -> str:
    return reverse(
        "api-v1:environments:experiments:experiment-metrics-detail",
        args=[environment.api_key, experiment.id, em.id],
    )


@pytest.fixture()
def metric(environment: Environment) -> Metric:
    metric: Metric = Metric.objects.create(
        environment=environment,
        name="Sessions per User",
        definition={"version": 1, "event": "session_started"},
    )
    return metric


def test_attach_metric__valid__returns_201(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    metric: Metric,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)

    # When
    response = admin_client_new.post(
        _list_url(environment, experiment),
        data={
            "metric": metric.id,
            "expected_direction": ExpectedDirection.INCREASE,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["metric_name"] == "Sessions per User"
    assert data["expected_direction"] == "increase"
    assert ExperimentMetric.objects.filter(
        experiment=experiment, metric=metric
    ).exists()


def test_attach_metric__same_metric_twice__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    metric: Metric,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When
    response = admin_client_new.post(
        _list_url(environment, experiment),
        data={"metric": metric.id, "expected_direction": ExpectedDirection.INCREASE},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_attach_metric__from_other_environment__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    project: "Project",
    enable_features: "EnableFeaturesFixture",
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
        _list_url(environment, experiment),
        data={"metric": foreign.id, "expected_direction": ExpectedDirection.INCREASE},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_list_metrics__with_attachment__returns_attached(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    metric: Metric,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When
    response = admin_client_new.get(_list_url(environment, experiment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body) == 1
    assert body[0]["metric"] == metric.id


def test_detach_metric__attached__returns_204(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    metric: Metric,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given
    enable_features(EXPERIMENT_FLAG)
    em = ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When
    response = admin_client_new.delete(_detail_url(environment, experiment, em))

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not ExperimentMetric.objects.filter(id=em.id).exists()


def test_update_attachment__new_direction__returns_200(
    admin_client_new: APIClient,
    environment: Environment,
    experiment: Experiment,
    metric: Metric,
    enable_features: "EnableFeaturesFixture",
) -> None:
    # Given an attached metric
    enable_features(EXPERIMENT_FLAG)
    em = ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When its expected direction is changed
    response = admin_client_new.patch(
        _detail_url(environment, experiment, em),
        data={"expected_direction": ExpectedDirection.DECREASE},
        format="json",
    )

    # Then the change is persisted
    assert response.status_code == status.HTTP_200_OK
    em.refresh_from_db()
    assert em.expected_direction == ExpectedDirection.DECREASE
