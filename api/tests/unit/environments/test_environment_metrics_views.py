import pytest
import random
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils import timezone

from features.models import Feature, FeatureState, FeatureSegment
from segments.models import Segment
from features.workflows.core.models import ChangeRequest
from users.models import FFAdminUser
from environments.models import Environment
from projects.models import Project
from tests.types import WithEnvironmentPermissionsCallable
from metrics.types import EnvMetrics
from common.environments.permissions import (
    VIEW_ENVIRONMENT,
)

def test_get_environment_metrics_without_workflows(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    url = reverse("api-v1:environments:environment-metrics-list", args=[environment.api_key])
    
    # When
    response = staff_client.get(url)
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert EnvMetrics.FEATURES.value in data
    assert EnvMetrics.SEGMENTS.value in data
    assert EnvMetrics.CHANGE_REQUESTS.value not in data
    assert EnvMetrics.SCHEDULED_CHANGES.value not in data

def test_get_environment_metrics_with_workflows(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    environment.minimum_change_request_approvals = 1
    environment.save()
    url = reverse("api-v1:environments:environment-metrics-list", args=[environment.api_key])
    
    # When
    response = staff_client.get(url)
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert EnvMetrics.CHANGE_REQUESTS.value in data
    assert EnvMetrics.SCHEDULED_CHANGES.value in data
    assert EnvMetrics.FEATURES.value in data
    assert EnvMetrics.SEGMENTS.value in data

@pytest.mark.parametrize("total_features, feature_enabled_count,segment_overrides_count, change_request_count, scheduled_change_count", [
    (0, 0, 0, 0, 0),
    (10, 4, 9, 4, 3),
    (10, 10, 10, 10, 10),
    (5, 10, 6, 3, 2),
    (21, 14, 8, 13, 2)
])
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
    test_environment = Environment.objects.create(name="My environment", project=project)
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    
    features = []
    version = 0
    for i in range(total_features):
        feature = Feature.objects.create(project=test_environment.project, name=f"Feature disabled {i}")
        FeatureState.objects.update_or_create(feature=feature, environment=test_environment, identity=None, enabled=False, version=version)
        features.append(feature)
        version += 1
    
    for i in range(min(feature_enabled_count, total_features)):
        targetFeature = features[i]
        FeatureState.objects.update_or_create(
            feature=targetFeature, 
            environment=test_environment, 
            identity=None, 
            enabled=True, 
            version=version
        )
        version += 1

    for i in range(segment_overrides_count):
        segment = Segment.objects.create(project=test_environment.project, name=f"Segment overrides {i}")
        targetFeature = random.choice(features)
        feature_segment = FeatureSegment.objects.create(feature=targetFeature, segment=segment, environment=test_environment)
        FeatureState.objects.update_or_create(feature=targetFeature, environment=test_environment, feature_segment=feature_segment, identity=None, enabled=False, version=version)
        version += 1

    for i in range(change_request_count):
        ChangeRequest.objects.create(environment=test_environment, title=f"Change request {i}", user_id=admin_user.id)
        version += 1
    for i in range(scheduled_change_count):
        FeatureState.objects.update_or_create(feature=random.choice(features), environment=test_environment, identity=None, enabled=True, live_from=timezone.now() + timedelta(days=5), version=version)
        version += 1

    test_environment.minimum_change_request_approvals = 1
    test_environment.save()

    url = reverse("api-v1:environments:environment-metrics-list", args=[test_environment.api_key])
    
    # When
    response = staff_client.get(url)
    
    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert len(data["features"]) == 2
    assert data["features"][0]["title"] == "total_features"
    assert data["features"][0]["value"] == total_features
    assert data["features"][1]["title"] == "enabled_features"
    assert data["features"][1]["value"] == min(feature_enabled_count, total_features)
    
    assert data["segments"][0]["title"] == "segment_overrides"
    assert data["segments"][0]["value"] == segment_overrides_count
    
    assert data["change_requests"][0]["title"] == "open_change_requests"
    assert data["change_requests"][0]["value"] == change_request_count

    assert data["scheduled_changes"][0]["title"] == "total_scheduled_changes"
    assert data["scheduled_changes"][0]["value"] == scheduled_change_count
    
