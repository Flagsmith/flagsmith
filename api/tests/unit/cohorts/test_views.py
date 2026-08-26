import pytest
from common.environments.permissions import (
    MANAGE_SEGMENT_OVERRIDES,
    VIEW_ENVIRONMENT,
)
from common.projects.permissions import MANAGE_SEGMENTS
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from cohorts.models import (
    Cohort,
    CohortMembership,
    CohortMembershipState,
    CohortSyncKey,
)
from environments.dynamodb import DynamoIdentityWrapper
from environments.models import Environment
from metadata.models import Metadata, MetadataModelField
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


def test_retrieve_cohort__mixed_membership_states__returns_membership_counts(
    staff_client: APIClient,
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT], environment_id=edge_cohort.environment_id
    )
    memberships = {
        "applied-1": CohortMembershipState.APPLIED,
        "applied-2": CohortMembershipState.APPLIED,
        "pending-add-1": CohortMembershipState.PENDING_ADD,
        "pending-remove-1": CohortMembershipState.PENDING_REMOVE,
    }
    CohortMembership.objects.bulk_create(
        CohortMembership(cohort=edge_cohort, identifier=identifier, state=state)
        for identifier, state in memberships.items()
    )
    url = reverse(
        "api-v1:environments:cohorts:cohorts-detail",
        args=[edge_cohort.environment.api_key, edge_cohort.id],
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["membership_counts"] == {
        "applied": 2,
        "pending_add": 1,
        "pending_remove": 1,
    }
    assert response.json()["last_synced_at"] is None


def test_update_cohort__staff_with_manage_segments__updates_segment_fields(
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
    response = staff_client.patch(
        url,
        data={"name": "renamed", "description": "Updated description"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    edge_cohort.segment.refresh_from_db()
    assert edge_cohort.segment.name == "renamed"
    assert edge_cohort.segment.description == "Updated description"
    assert response.json()["name"] == "renamed"
    assert response.json()["description"] == "Updated description"


def test_update_cohort__staff_without_permission__returns_403(
    staff_client: APIClient,
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT], environment_id=edge_cohort.environment_id
    )
    url = reverse(
        "api-v1:environments:cohorts:cohorts-detail",
        args=[edge_cohort.environment.api_key, edge_cohort.id],
    )

    # When
    response = staff_client.patch(url, data={"name": "renamed"}, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    edge_cohort.segment.refresh_from_db()
    assert edge_cohort.segment.name != "renamed"


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


def test_create_sync_key__user_or_master_api_key__returns_201_with_plaintext_key(
    admin_client_new: APIClient,
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    environment = dynamo_enabled_project_environment_one
    url = reverse(
        "api-v1:environments:cohorts:sync-keys-list", args=[environment.api_key]
    )

    # When
    response = admin_client_new.post(
        url, data={"name": "Amplitude prod"}, format="json"
    )

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
    admin_client_new: APIClient,
    environment: Environment,
) -> None:
    # Given
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
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert [(row["name"], row["key"]) for row in response.json()] == [("live", None)]


def test_delete_sync_key__existing_key__revokes(
    admin_client_new: APIClient,
    environment: Environment,
) -> None:
    # Given
    key, _ = CohortSyncKey.objects.create_key(name="old", environment=environment)
    url = reverse(
        "api-v1:environments:cohorts:sync-keys-detail",
        args=[environment.api_key, key.prefix],
    )

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    key.refresh_from_db()
    assert key.revoked is True


def test_create_sync_key__missing_name__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:cohorts:sync-keys-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client_new.post(url, data={}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not CohortSyncKey.objects.exists()


def test_create_cohort__with_metadata__attaches_metadata_to_segment(
    staff_client: APIClient,
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    required_segment_metadata_field_for_dynamo_project: MetadataModelField,
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
        data={
            "name": "Beta users",
            "metadata": [
                {
                    "model_field": required_segment_metadata_field_for_dynamo_project.id,
                    "field_value": 10,
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    cohort = Cohort.objects.get(id=response.json()["id"])
    metadata = Metadata.objects.get(
        model_field=required_segment_metadata_field_for_dynamo_project
    )
    assert metadata.object_id == cohort.segment_id
    assert metadata.field_value == "10"


def test_create_cohort__missing_required_metadata__returns_400(
    staff_client: APIClient,
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    required_segment_metadata_field_for_dynamo_project: MetadataModelField,
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
    response = staff_client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["metadata"] == ["Missing required metadata field: a"]
    assert not Cohort.objects.exists()


def test_sync_csv__staff_with_manage_segments__returns_202_with_counts(
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
        "api-v1:environments:cohorts:cohorts-sync-csv",
        args=[edge_cohort.environment.api_key, edge_cohort.id],
    )
    file = SimpleUploadedFile(
        "identities.csv",
        b"identity,email\nuser-1,a@example.com\nuser-2,b@example.com\nuser-3,\n",
        content_type="text/csv",
    )

    # When
    response = staff_client.post(
        url,
        data={"file": file, "identifier_column": 1, "has_header": True},
        format="multipart",
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        "version": 1,
        "added": 2,
        "removed": 0,
        "unchanged": 0,
        "ignored": {"empty": 1, "duplicates": 0, "too_long": 0},
    }
    memberships = CohortMembership.objects.filter(cohort=edge_cohort)
    assert {m.identifier for m in memberships} == {
        "a@example.com",
        "b@example.com",
    }
    assert all(m.state == CohortMembershipState.APPLIED for m in memberships)
    edge_cohort.refresh_from_db()
    assert edge_cohort.version == 1
    assert edge_cohort.last_synced_at is not None


def test_sync_csv__without_permission__returns_403(
    staff_client: APIClient,
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT], environment_id=edge_cohort.environment_id
    )
    url = reverse(
        "api-v1:environments:cohorts:cohorts-sync-csv",
        args=[edge_cohort.environment.api_key, edge_cohort.id],
    )
    file = SimpleUploadedFile("identities.csv", b"user-1\n", content_type="text/csv")

    # When
    response = staff_client.post(url, data={"file": file}, format="multipart")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not CohortMembership.objects.exists()


def test_sync_csv__file_over_size_limit__returns_413(
    staff_client: APIClient,
    dynamo_enabled_project: Project,
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("cohorts.serializers.COHORT_CSV_MAX_FILE_SIZE_BYTES", 10)
    with_project_permissions(  # type: ignore[call-arg]
        [MANAGE_SEGMENTS], project_id=dynamo_enabled_project.id
    )
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_SEGMENT_OVERRIDES],
        environment_id=edge_cohort.environment_id,
    )
    url = reverse(
        "api-v1:environments:cohorts:cohorts-sync-csv",
        args=[edge_cohort.environment.api_key, edge_cohort.id],
    )
    file = SimpleUploadedFile(
        "identities.csv", b"identity\nuser-1\n", content_type="text/csv"
    )

    # When
    response = staff_client.post(url, data={"file": file}, format="multipart")

    # Then
    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    assert not CohortMembership.objects.exists()


def test_sync_csv__no_valid_identifiers__returns_400(
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
        "api-v1:environments:cohorts:cohorts-sync-csv",
        args=[edge_cohort.environment.api_key, edge_cohort.id],
    )
    file = SimpleUploadedFile("identities.csv", b"identity\n", content_type="text/csv")

    # When
    response = staff_client.post(url, data={"file": file}, format="multipart")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"file": "No valid identifiers found in the CSV file."}
    assert not CohortMembership.objects.exists()
    edge_cohort.refresh_from_db()
    assert edge_cohort.version == 0


def test_sync_csv__deletion_requested_cohort__returns_404(
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
    edge_cohort.deletion_requested_at = timezone.now()
    edge_cohort.save(update_fields=["deletion_requested_at"])
    url = reverse(
        "api-v1:environments:cohorts:cohorts-sync-csv",
        args=[edge_cohort.environment.api_key, edge_cohort.id],
    )
    file = SimpleUploadedFile("identities.csv", b"user-1\n", content_type="text/csv")

    # When
    response = staff_client.post(url, data={"file": file}, format="multipart")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
