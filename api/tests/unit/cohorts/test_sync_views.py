import typing

from django.urls import reverse
from django.utils import timezone
from flag_engine.segments.constants import IS_SET
from pytest_django.fixtures import SettingsWrapper
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from cohorts.models import (
    Cohort,
    CohortMembership,
    CohortMembershipState,
    CohortSourceType,
    CohortSyncKey,
)
from environments.dynamodb import DynamoIdentityWrapper
from environments.models import Environment

_KeyAndPlaintext = typing.Tuple[CohortSyncKey, str]


def _authenticated_client(plaintext_key: str) -> APIClient:
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {plaintext_key}")
    return client


def test_amplitude_create_list__valid_key__creates_amplitude_cohort(
    cohort_sync_key: _KeyAndPlaintext,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    key, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = client.post(
        url, data={"name": "[Amplitude] Beta users: 1234"}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    cohort = Cohort.objects.get(uuid=response.json()["list_id"])
    assert cohort.environment == key.environment
    assert cohort.source_type == CohortSourceType.AMPLITUDE
    assert cohort.segment.name == "[Amplitude] Beta users: 1234"
    condition = cohort.segment.rules.get().conditions.get()
    assert condition.operator == IS_SET
    assert condition.property == cohort.system_trait_key


def test_amplitude_create_list__postgres_environment__creates_cohort(
    environment: Environment,
) -> None:
    # Given - an environment whose identities live in Postgres
    _, plaintext = CohortSyncKey.objects.create_key(
        name="postgres key", environment=environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    cohort = Cohort.objects.get(uuid=response.json()["list_id"])
    assert cohort.environment == environment


def test_amplitude_create_list__missing_credentials__returns_401(
    db: None,
) -> None:
    # Given
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = APIClient().post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_amplitude_create_list__unknown_key__returns_401(
    db: None,
) -> None:
    # Given
    client = _authenticated_client("not-a-key")
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_amplitude_create_list__revoked_key__returns_401(
    cohort_sync_key: _KeyAndPlaintext,
) -> None:
    # Given
    key, plaintext = cohort_sync_key
    key.revoked = True
    key.save()
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_amplitude_add_members__new_identifiers__applies_memberships(
    cohort_sync_key: _KeyAndPlaintext,
    amplitude_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-add", kwargs={"pk": str(amplitude_cohort.uuid)}
    )

    # When
    response = client.post(
        url, data={"user_ids": ["user-1", "user-2", "user-1"]}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert sorted(
        CohortMembership.objects.filter(cohort=amplitude_cohort).values_list(
            "identifier", "state"
        )
    ) == [
        ("user-1", CohortMembershipState.APPLIED),
        ("user-2", CohortMembershipState.APPLIED),
    ]
    api_key = amplitude_cohort.environment.api_key
    document = dynamodb_identity_wrapper.get_item(f"{api_key}_user-1")
    assert document is not None
    assert document["system_traits"] == {amplitude_cohort.system_trait_key: True}


def test_amplitude_add_members__applied_member__stays_applied(
    cohort_sync_key: _KeyAndPlaintext,
    amplitude_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    _, plaintext = cohort_sync_key
    CohortMembership.objects.create(
        cohort=amplitude_cohort,
        identifier="user-1",
        state=CohortMembershipState.APPLIED,
    )
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-add", kwargs={"pk": str(amplitude_cohort.uuid)}
    )

    # When
    response = client.post(url, data={"user_ids": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    membership = CohortMembership.objects.get(cohort=amplitude_cohort)
    assert (membership.identifier, membership.state) == (
        "user-1",
        CohortMembershipState.APPLIED,
    )


def test_amplitude_remove_members__applied_member__unsets_trait_and_deletes_row(
    cohort_sync_key: _KeyAndPlaintext,
    amplitude_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    api_key = amplitude_cohort.environment.api_key
    trait_key = amplitude_cohort.system_trait_key
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": f"{api_key}_member",
            "identifier": "member",
            "environment_api_key": api_key,
            "system_traits": {trait_key: True},
        }
    )
    CohortMembership.objects.create(
        cohort=amplitude_cohort,
        identifier="member",
        state=CohortMembershipState.APPLIED,
    )
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-remove",
        kwargs={"pk": str(amplitude_cohort.uuid)},
    )

    # When
    response = client.post(url, data={"user_ids": ["member"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert not CohortMembership.objects.filter(cohort=amplitude_cohort).exists()
    document = dynamodb_identity_wrapper.get_item(f"{api_key}_member")
    assert document is not None
    assert document["system_traits"] == {}


def test_amplitude_remove_members__unknown_identifier__no_rows_created(
    cohort_sync_key: _KeyAndPlaintext,
    amplitude_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-remove",
        kwargs={"pk": str(amplitude_cohort.uuid)},
    )

    # When
    response = client.post(url, data={"user_ids": ["stranger"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert not CohortMembership.objects.filter(cohort=amplitude_cohort).exists()


def test_amplitude_add_members__csv_cohort__returns_404(
    cohort_sync_key: _KeyAndPlaintext,
    edge_cohort: Cohort,
) -> None:
    # Given - an edge cohort whose source is CSV, not Amplitude
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-add", kwargs={"pk": str(edge_cohort.uuid)}
    )

    # When
    response = client.post(url, data={"user_ids": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_amplitude_add_members__other_environment_cohort__returns_404(
    amplitude_cohort: Cohort,
    dynamo_enabled_project_environment_two: Environment,
) -> None:
    # Given - a valid key scoped to a different environment
    _, plaintext = CohortSyncKey.objects.create_key(
        name="other env", environment=dynamo_enabled_project_environment_two
    )
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-add", kwargs={"pk": str(amplitude_cohort.uuid)}
    )

    # When
    response = client.post(url, data={"user_ids": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_amplitude_add_members__deletion_requested_cohort__returns_404(
    cohort_sync_key: _KeyAndPlaintext,
    amplitude_cohort: Cohort,
) -> None:
    # Given
    amplitude_cohort.deletion_requested_at = timezone.now()
    amplitude_cohort.save(update_fields=["deletion_requested_at"])
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-add", kwargs={"pk": str(amplitude_cohort.uuid)}
    )

    # When
    response = client.post(url, data={"user_ids": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_amplitude_add_members__malformed_list_id__returns_404(
    cohort_sync_key: _KeyAndPlaintext,
) -> None:
    # Given
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:amplitude-add", kwargs={"pk": "not-a-uuid"})

    # When
    response = client.post(url, data={"user_ids": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_amplitude_add_members__empty_user_ids__returns_400(
    cohort_sync_key: _KeyAndPlaintext,
    amplitude_cohort: Cohort,
) -> None:
    # Given
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-add", kwargs={"pk": str(amplitude_cohort.uuid)}
    )

    # When
    response = client.post(url, data={"user_ids": []}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_amplitude_create_list__valid_key__audits_and_queues_environment_update(
    cohort_sync_key: _KeyAndPlaintext,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    key, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = client.post(url, data={"name": "Beta users"}, format="json")

    # Then - the audit record carries no user, names the source, and is the
    # hook that rebuilds the environment document.
    assert response.status_code == status.HTTP_200_OK
    cohort = Cohort.objects.get(uuid=response.json()["list_id"])
    audit_log = AuditLog.objects.get(related_object_id=cohort.segment_id)
    assert audit_log.author is None
    assert audit_log.master_api_key is None
    assert audit_log.environment == key.environment
    assert audit_log.related_object_type == RelatedObjectType.SEGMENT.name
    assert audit_log.log == (
        "New Segment created: Beta users (via Amplitude cohort sync)"
    )
    assert audit_log.environment_document_updated is True


def test_amplitude_create_list__valid_key__history_records_no_user(
    cohort_sync_key: _KeyAndPlaintext,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = client.post(url, data={"name": "Beta users"}, format="json")

    # Then - a machine caller leaves no user on historical records; stamping
    # one would fail, since the sync key is not a Flagsmith user.
    assert response.status_code == status.HTTP_200_OK
    cohort = Cohort.objects.get(uuid=response.json()["list_id"])
    history_record = cohort.segment.history.get()
    assert history_record.history_user is None
    assert history_record.master_api_key is None


def test_amplitude_add_members__master_api_key_throttle_enabled__succeeds(
    cohort_sync_key: _KeyAndPlaintext,
    amplitude_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    settings: SettingsWrapper,
) -> None:
    # Given - the throttle that reads master API key attributes off the caller
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": ["core.throttling.MasterAPIKeyUserRateThrottle"],
        "DEFAULT_THROTTLE_RATES": {"master_api_key": "1000/minute"},
    }
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-add", kwargs={"pk": str(amplitude_cohort.uuid)}
    )

    # When
    response = client.post(url, data={"user_ids": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_amplitude_add_members__identifier_over_1024_bytes__returns_400(
    cohort_sync_key: _KeyAndPlaintext,
    amplitude_cohort: Cohort,
) -> None:
    # Given - 512 three-byte characters: few characters, too many bytes
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:amplitude-add", kwargs={"pk": str(amplitude_cohort.uuid)}
    )

    # When
    response = client.post(url, data={"user_ids": ["€" * 512]}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "1024 bytes" in str(response.json())
    assert not CohortMembership.objects.exists()
