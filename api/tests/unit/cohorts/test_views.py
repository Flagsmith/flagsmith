import pytest
from common.environments.permissions import VIEW_ENVIRONMENT
from common.projects.permissions import MANAGE_SEGMENTS
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from cohorts.models import Cohort
from environments.models import Environment
from organisations.models import Subscription
from segments.models import Segment
from tests.types import (
    WithEnvironmentPermissionsCallable,
    WithProjectPermissionsCallable,
)


def test_create_cohort__staff_with_manage_segments__returns_201(
    staff_client: APIClient,
    environment: Environment,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:cohorts:cohorts-list", args=[environment.api_key]
    )

    # When
    response = staff_client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    cohort = Cohort.objects.get(id=response.json()["id"])
    assert response.json()["name"] == "Beta users"
    assert response.json()["segment"] == cohort.segment_id
    assert cohort.environment == environment


def test_create_cohort__staff_without_permission__returns_403(
    staff_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:cohorts:cohorts-list", args=[environment.api_key]
    )

    # When
    response = staff_client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_cohort__unknown_environment__returns_403(
    staff_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:environments:cohorts:cohorts-list", args=["missing-key"])

    # When
    response = staff_client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_cohorts__deletion_requested_cohort__excluded(
    staff_client: APIClient,
    environment: Environment,
    cohort: Cohort,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    deleting_segment = Segment.objects.create(
        name="going away", project=environment.project
    )
    Cohort.objects.create(
        environment=environment,
        segment=deleting_segment,
        deletion_requested_at=timezone.now(),
    )
    url = reverse(
        "api-v1:environments:cohorts:cohorts-list", args=[environment.api_key]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert [row["id"] for row in response.json()] == [cohort.id]
    assert response.json()[0]["name"] == cohort.segment.name


def test_delete_cohort__staff_with_manage_segments__returns_202(
    staff_client: APIClient,
    environment: Environment,
    cohort: Cohort,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:cohorts:cohorts-detail",
        args=[environment.api_key, cohort.id],
    )

    # When
    response = staff_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert not Cohort.objects.filter(id=cohort.id).exists()


@pytest.mark.saas_mode
def test_create_cohort__saas_free_plan__returns_403(
    staff_client: APIClient,
    environment: Environment,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:cohorts:cohorts-list", args=[environment.api_key]
    )

    # When
    response = staff_client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == (
        "This resource requires a START_UP plan or above."
    )


@pytest.mark.saas_mode
def test_create_cohort__saas_startup_plan__returns_201(
    staff_client: APIClient,
    environment: Environment,
    with_project_permissions: WithProjectPermissionsCallable,
    startup_subscription: Subscription,
) -> None:
    # Given
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:cohorts:cohorts-list", args=[environment.api_key]
    )

    # When
    response = staff_client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
