import pytest
from common.environments.permissions import (
    VIEW_ENVIRONMENT,
)
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from tests.types import WithEnvironmentPermissionsCallable


@pytest.mark.parametrize("with_workflows", [True, False])
def test_get_environment_metrics_without_workflows(
    admin_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    with_workflows: bool,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    environment.minimum_change_request_approvals = 1 if with_workflows else None
    environment.save()
    url = reverse(
        "api-v1:environments:environment-metrics-list", args=[environment.api_key]
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "metrics" in data
    names = [item["name"] for item in data["metrics"]]
    assert "total_features" in names
    assert "enabled_features" in names
    assert "segment_overrides" in names
    if with_workflows:
        assert "open_change_requests" in names
        assert "total_scheduled_changes" in names
    else:
        assert "open_change_requests" not in names
        assert "total_scheduled_changes" not in names


def test_environment_metrics_requires_permission(
    staff_client: APIClient,
    environment: Environment,
) -> None:
    # Given: No permissions are set for the user
    url = reverse(
        "api-v1:environments:environment-metrics-list", args=[environment.api_key]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
