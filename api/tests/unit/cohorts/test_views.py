import pytest
from common.environments.permissions import (
    MANAGE_SEGMENT_OVERRIDES,
    VIEW_ENVIRONMENT,
)
from common.projects.permissions import MANAGE_SEGMENTS
from django.urls import reverse
from django.utils import timezone
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from cohorts.models import Cohort, CohortSyncKey
from environments.dynamodb import DynamoIdentityWrapper
from environments.models import Environment
from organisations.models import Subscription
from projects.models import Project
from segments.models import Segment
from tests.types import (
    WithEnvironmentPermissionsCallable,
    WithProjectPermissionsCallable,
)


def test_create_cohort__staff_with_manage_segments__returns_201(
    staff_client: APIClient,
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_project_permissions(  # type: ignore[call-arg]
        [MANAGE_SEGMENTS], project_id=dynamo_enabled_project.id
    )
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_SEGMENT_OVERRIDES],
        environment_id=dynamo_enabled_project_environment_one.id,
    )
    url = reverse(
        "api-v1:environments:cohorts:cohorts-list",
        args=[dynamo_enabled_project_environment_one.api_key],
    )

    # When
    response = staff_client.post(
        url,
        data={"name": "Beta users", "description": "Early access group"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    cohort = Cohort.objects.get(id=response.json()["id"])
    assert response.json()["name"] == "Beta users"
    assert response.json()["description"] == "Early access group"
    assert cohort.segment.description == "Early access group"
    assert response.json()["segment"] == cohort.segment_id
    assert cohort.environment == dynamo_enabled_project_environment_one


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


def test_create_cohort__manage_segments_without_environment_access__returns_403(
    staff_client: APIClient,
    environment: Environment,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given - project-level segment rights, but no access to the environment
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:cohorts:cohorts-list", args=[environment.api_key]
    )

    # When
    response = staff_client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_cohort__without_manage_segment_overrides__returns_403(
    staff_client: APIClient,
    environment: Environment,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given - segment rights and environment access, but no override rights
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
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
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    environment = edge_cohort.environment
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT], environment_id=environment.id
    )
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
    assert [row["id"] for row in response.json()] == [edge_cohort.id]
    assert response.json()[0]["name"] == edge_cohort.segment.name


def test_delete_cohort__staff_with_manage_segments__returns_202(
    staff_client: APIClient,
    dynamo_enabled_project: Project,
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_project_permissions(  # type: ignore[call-arg]
        [MANAGE_SEGMENTS], project_id=dynamo_enabled_project.id
    )
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_SEGMENT_OVERRIDES],
        environment_id=edge_cohort.environment_id,
    )
    url = reverse(
        "api-v1:environments:cohorts:cohorts-detail",
        args=[edge_cohort.environment.api_key, edge_cohort.id],
    )

    # When
    response = staff_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert not Cohort.objects.filter(id=edge_cohort.id).exists()


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


def test_create_cohort__saas_startup_plan__returns_201(
    staff_client: APIClient,
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    startup_subscription: Subscription,
    mocker: MockerFixture,
) -> None:
    # Given (saas_mode's fake filesystem breaks moto, so patch is_saas instead)
    mocker.patch("organisations.subscriptions.permissions.is_saas", return_value=True)
    with_project_permissions(  # type: ignore[call-arg]
        [MANAGE_SEGMENTS], project_id=dynamo_enabled_project.id
    )
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_SEGMENT_OVERRIDES],
        environment_id=dynamo_enabled_project_environment_one.id,
    )
    url = reverse(
        "api-v1:environments:cohorts:cohorts-list",
        args=[dynamo_enabled_project_environment_one.api_key],
    )

    # When
    response = staff_client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_create_cohort__non_edge_project__returns_201(
    staff_client: APIClient,
    environment: Environment,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given - a project whose identities live in Postgres
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_SEGMENT_OVERRIDES]
    )
    url = reverse(
        "api-v1:environments:cohorts:cohorts-list", args=[environment.api_key]
    )

    # When
    response = staff_client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert Cohort.objects.get(id=response.json()["id"]).environment == environment


def test_create_sync_key__staff_with_permissions__returns_201_with_plaintext_key(
    staff_client: APIClient,
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    environment = dynamo_enabled_project_environment_one
    with_project_permissions(  # type: ignore[call-arg]
        [MANAGE_SEGMENTS], project_id=dynamo_enabled_project.id
    )
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_SEGMENT_OVERRIDES],
        environment_id=environment.id,
    )
    url = reverse(
        "api-v1:environments:cohorts:sync-keys-list", args=[environment.api_key]
    )

    # When
    response = staff_client.post(url, data={"name": "Amplitude prod"}, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    key = CohortSyncKey.objects.get(environment=environment)
    assert response.json()["prefix"] == key.prefix
    assert response.json()["key"].startswith(key.prefix)
    assert key.name == "Amplitude prod"


def test_create_sync_key__staff_without_permission__returns_403(
    staff_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:cohorts:sync-keys-list", args=[environment.api_key]
    )

    # When
    response = staff_client.post(url, data={"name": "Amplitude prod"}, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_sync_keys__revoked_key__excluded_and_plaintext_never_returned(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    CohortSyncKey.objects.create_key(name="live", environment=environment)
    revoked, _ = CohortSyncKey.objects.create_key(
        name="revoked", environment=environment
    )
    revoked.revoked = True
    revoked.save()
    url = reverse(
        "api-v1:environments:cohorts:sync-keys-list", args=[environment.api_key]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert [(row["name"], row["key"]) for row in response.json()] == [("live", None)]


def test_delete_sync_key__existing_key__revokes(
    staff_client: APIClient,
    environment: Environment,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_SEGMENT_OVERRIDES]
    )
    key, _ = CohortSyncKey.objects.create_key(name="old", environment=environment)
    url = reverse(
        "api-v1:environments:cohorts:sync-keys-detail",
        args=[environment.api_key, key.prefix],
    )

    # When
    response = staff_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    key.refresh_from_db()
    assert key.revoked is True


def test_create_sync_key__missing_name__returns_400(
    staff_client: APIClient,
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_project_permissions(  # type: ignore[call-arg]
        [MANAGE_SEGMENTS], project_id=dynamo_enabled_project.id
    )
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_SEGMENT_OVERRIDES],
        environment_id=dynamo_enabled_project_environment_one.id,
    )
    url = reverse(
        "api-v1:environments:cohorts:sync-keys-list",
        args=[dynamo_enabled_project_environment_one.api_key],
    )

    # When
    response = staff_client.post(url, data={}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not CohortSyncKey.objects.exists()


def test_create_sync_key__non_edge_project__returns_400(
    staff_client: APIClient,
    environment: Environment,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_SEGMENT_OVERRIDES]
    )
    url = reverse(
        "api-v1:environments:cohorts:sync-keys-list", args=[environment.api_key]
    )

    # When
    response = staff_client.post(url, data={"name": "Amplitude prod"}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Dynamo DB is not enabled for this project"
    assert not CohortSyncKey.objects.exists()
