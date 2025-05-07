import random
from datetime import timedelta

import pytest
from common.environments.permissions import (
    VIEW_ENVIRONMENT,
)
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.workflows.core.models import ChangeRequest
from metrics.types import EnvMetricsName
from projects.models import Project
from segments.models import Segment
from tests.types import WithEnvironmentPermissionsCallable
from users.models import FFAdminUser


def test_get_environment_metrics_without_workflows(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:environment-metrics-list", args=[environment.api_key]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "metrics" in data
    names = [item["name"] for item in data["metrics"]]
    assert "open_change_requests" not in names
    assert "total_scheduled_changes" not in names
    assert "total_features" in names
    assert "enabled_features" in names
    assert "segment_overrides" in names


def test_get_environment_metrics_with_workflows(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    environment.minimum_change_request_approvals = 1
    environment.save()
    url = reverse(
        "api-v1:environments:environment-metrics-list", args=[environment.api_key]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "metrics" in data
    names = [item["name"] for item in data["metrics"]]
    assert "open_change_requests" in names
    assert "total_scheduled_changes" in names
    assert "total_features" in names
    assert "enabled_features" in names
    assert "segment_overrides" in names


@pytest.mark.parametrize(
    "total_features, feature_enabled_count,segment_overrides_count, change_request_count, scheduled_change_count",
    [
        (0, 0, 0, 0, 0),
        (10, 4, 9, 4, 3),
        (10, 10, 10, 10, 10),
        (5, 10, 6, 3, 2),
        (21, 14, 8, 13, 2),
    ],
)
def test_get_environment_metrics_correctly_computes_data(
    staff_client: APIClient,
    admin_user: FFAdminUser,
    project: Project,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    total_features: int,
    feature_enabled_count: int,
    segment_overrides_count: int,
    change_request_count: int,
    scheduled_change_count: int,
) -> None:
    # Given
    env = Environment.objects.create(name="env", project=project)
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]

    features = []
    version = 0
    for i in range(total_features):
        f = Feature.objects.create(project=project, name=f"f-{i}")
        FeatureState.objects.update_or_create(
            feature=f, environment=env, identity=None, enabled=False, version=version
        )
        features.append(f)
        version += 1

    for i in range(min(feature_enabled_count, total_features)):
        FeatureState.objects.update_or_create(
            feature=features[i],
            environment=env,
            identity=None,
            enabled=True,
            version=version,
        )
        version += 1

    for i in range(segment_overrides_count):
        segment = Segment.objects.create(project=project, name=f"s-{i}")
        f = random.choice(features)
        fs = FeatureSegment.objects.create(feature=f, segment=segment, environment=env)
        FeatureState.objects.update_or_create(
            feature=f,
            environment=env,
            feature_segment=fs,
            identity=None,
            enabled=False,
            version=version,
        )
        version += 1

    for i in range(change_request_count):
        ChangeRequest.objects.create(
            environment=env, title=f"CR-{i}", user_id=admin_user.id
        )
        version += 1

    for i in range(scheduled_change_count):
        FeatureState.objects.update_or_create(
            feature=random.choice(features),
            environment=env,
            identity=None,
            enabled=True,
            live_from=timezone.now() + timedelta(days=5),
            version=version,
        )
        version += 1

    env.minimum_change_request_approvals = 1
    env.save()

    url = reverse("api-v1:environments:environment-metrics-list", args=[env.api_key])

    # When
    res = staff_client.get(url)

    # Then
    assert res.status_code == status.HTTP_200_OK
    metrics = res.json()["metrics"]

    def get_metric_value(name: str) -> int:
        return next((m["value"] for m in metrics if m["name"] == name), 0)

    assert get_metric_value(EnvMetricsName.TOTAL_FEATURES.value) == total_features
    assert get_metric_value(EnvMetricsName.ENABLED_FEATURES.value) == min(
        feature_enabled_count, total_features
    )
    assert (
        get_metric_value(EnvMetricsName.SEGMENT_OVERRIDES.value)
        == segment_overrides_count
    )
    assert (
        get_metric_value(EnvMetricsName.OPEN_CHANGE_REQUESTS.value)
        == change_request_count
    )
    assert (
        get_metric_value(EnvMetricsName.TOTAL_SCHEDULED_CHANGES.value)
        == scheduled_change_count
    )
