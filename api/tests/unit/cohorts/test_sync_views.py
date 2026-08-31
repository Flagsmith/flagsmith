import base64
import typing

import pytest
from django.urls import reverse
from django.utils import timezone
from flag_engine.segments.constants import IS_SET
from pytest_django.fixtures import SettingsWrapper
from pytest_structlog import StructuredLogCapture
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
from environments.identities.models import Identity
from environments.models import Environment
from projects.models import Project
from segments.models import Segment

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
    # Without ?shape=, the body carries the list ID at every spelling and
    # depth Amplitude might read.
    body = response.json()
    assert (
        body["listId"]
        == body["response"]["list_id"]
        == body["response"]["listId"]
        == body["list_id"]
    )
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


@pytest.mark.saas_mode
def test_amplitude_create_list__saas_free_plan__returns_403(
    cohort_sync_key: _KeyAndPlaintext,
) -> None:
    # Given
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == (
        "This resource requires a START_UP plan or above."
    )


def test_amplitude_create_list__segment_limit_reached__returns_400(
    cohort_sync_key: _KeyAndPlaintext,
    dynamo_enabled_project: Project,
    segment: Segment,
    settings: SettingsWrapper,
) -> None:
    # Given - the project already holds as many segments as the plan allows
    settings.EDGE_ENABLED = True
    dynamo_enabled_project.max_segments_allowed = 1
    dynamo_enabled_project.save()
    Segment.objects.create(name="existing", project=dynamo_enabled_project)
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = client.post(url, data={"name": "Beta users"}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["project"] == [
        "The project has reached the maximum allowed segments limit."
    ]
    assert not Cohort.objects.exists()


def _basic_auth_client(plaintext_key: str) -> APIClient:
    credentials = base64.b64encode(f"flagsmith:{plaintext_key}".encode()).decode()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Basic {credentials}")
    return client


def test_mixpanel_webhook__members_action_unknown_cohort__creates_cohort_and_memberships(
    postgres_cohort_sync_key: _KeyAndPlaintext,
) -> None:
    # Given
    key, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [
                    {"mixpanel_distinct_id": "user-1"},
                    {"mixpanel_distinct_id": "user-2"},
                ],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"action": "members", "status": "success"}
    cohort = Cohort.objects.get(
        environment=key.environment,
        source_type=CohortSourceType.MIXPANEL,
        external_id="mp-42",
    )
    assert cohort.segment.name == "Power users"
    assert sorted(
        CohortMembership.objects.filter(cohort=cohort).values_list(
            "identifier", "state"
        )
    ) == [
        ("user-1", CohortMembershipState.APPLIED),
        ("user-2", CohortMembershipState.APPLIED),
    ]


def test_mixpanel_webhook__members_action_existing_cohort__adds_to_it(
    postgres_cohort_sync_key: _KeyAndPlaintext,
    mixpanel_cohort: Cohort,
) -> None:
    # Given
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": "user-1"}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert Cohort.objects.filter(source_type=CohortSourceType.MIXPANEL).count() == 1
    membership = CohortMembership.objects.get(cohort=mixpanel_cohort)
    assert (membership.identifier, membership.state) == (
        "user-1",
        CohortMembershipState.APPLIED,
    )


def test_mixpanel_webhook__add_members_action__sets_system_trait(
    postgres_cohort_sync_key: _KeyAndPlaintext,
    mixpanel_cohort: Cohort,
) -> None:
    # Given
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "add_members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": "user-1"}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"action": "add_members", "status": "success"}
    identity = Identity.objects.get(
        environment=mixpanel_cohort.environment, identifier="user-1"
    )
    assert identity.system_traits == {mixpanel_cohort.system_trait_key: True}


def test_mixpanel_webhook__remove_members_action__unsets_system_trait(
    postgres_cohort_sync_key: _KeyAndPlaintext,
    mixpanel_cohort: Cohort,
) -> None:
    # Given
    Identity.objects.create(
        environment=mixpanel_cohort.environment,
        identifier="member",
        system_traits={mixpanel_cohort.system_trait_key: True},
    )
    CohortMembership.objects.create(
        cohort=mixpanel_cohort,
        identifier="member",
        state=CohortMembershipState.APPLIED,
    )
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "remove_members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": "member"}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"action": "remove_members", "status": "success"}
    assert not CohortMembership.objects.filter(cohort=mixpanel_cohort).exists()
    identity = Identity.objects.get(
        environment=mixpanel_cohort.environment, identifier="member"
    )
    assert identity.system_traits == {}


def test_mixpanel_webhook__add_members_unknown_cohort__returns_404_failure(
    postgres_cohort_sync_key: _KeyAndPlaintext,
    log: StructuredLogCapture,
) -> None:
    # Given
    key, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "add_members",
            "parameters": {
                "mixpanel_cohort_id": "unknown",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": "user-1"}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "action": "add_members",
        "status": "failure",
        "error": {"message": "Cohort not found.", "code": 404},
    }
    assert log.events == [
        {
            "level": "warning",
            "event": "sync_webhook.rejected",
            "source": "mixpanel",
            "action": "add_members",
            "environment__id": key.environment_id,
            "error__message": "Cohort not found.",
            "error__code": 404,
        }
    ]


def test_mixpanel_webhook__deletion_requested_cohort__returns_404_failure(
    postgres_cohort_sync_key: _KeyAndPlaintext,
    mixpanel_cohort: Cohort,
) -> None:
    # Given
    mixpanel_cohort.deletion_requested_at = timezone.now()
    mixpanel_cohort.save()
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "remove_members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": "user-1"}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["status"] == "failure"


def test_mixpanel_webhook__missing_parameters__returns_400_failure(
    postgres_cohort_sync_key: _KeyAndPlaintext,
) -> None:
    # Given
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(url, data={"action": "members"}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["action"] == "members"
    assert body["status"] == "failure"
    assert body["error"]["code"] == 400
    assert "parameters" in body["error"]["message"]


def test_mixpanel_webhook__non_object_payload__returns_400_failure(
    postgres_cohort_sync_key: _KeyAndPlaintext,
) -> None:
    # Given
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(url, data=["not", "an", "object"], format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["action"] is None
    assert body["status"] == "failure"
    assert body["error"]["code"] == 400


def test_mixpanel_webhook__unparseable_body__returns_400_failure(
    postgres_cohort_sync_key: _KeyAndPlaintext,
) -> None:
    # Given
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(url, data="{not json", content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "action": None,
        "status": "failure",
        "error": {"message": "Invalid payload.", "code": 400},
    }


def test_mixpanel_webhook__other_environment_key__returns_404_failure(
    mixpanel_cohort: Cohort,
) -> None:
    # Given - a key scoped to a different environment than the cohort's
    other_environment = Environment.objects.create(
        name="Other environment", project=mixpanel_cohort.environment.project
    )
    _, plaintext = CohortSyncKey.objects.create_key(
        name="other key", environment=other_environment
    )
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "add_members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": "user-1"}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert not CohortMembership.objects.filter(cohort=mixpanel_cohort).exists()


def test_mixpanel_webhook__empty_members_page__returns_success(
    postgres_cohort_sync_key: _KeyAndPlaintext,
) -> None:
    # Given
    key, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Empty cohort",
                "members": [],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    cohort = Cohort.objects.get(environment=key.environment, external_id="mp-42")
    assert not CohortMembership.objects.filter(cohort=cohort).exists()


def test_mixpanel_webhook__non_ascii_basic_credentials__returns_401(
    db: None,
) -> None:
    # Given - a header byte outside ASCII, which base64 decoding rejects
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Basic dXNlcjprÿZXk=")
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(url, data={"action": "members"}, format="json")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_mixpanel_webhook__nul_byte_in_basic_password__returns_401(
    db: None,
) -> None:
    # Given - valid base64 whose decoded password contains a NUL character
    credentials = base64.b64encode(b"user:\x00key").decode()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Basic {credentials}")
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(url, data={"action": "members"}, format="json")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_mixpanel_webhook__malformed_basic_credentials__returns_401(
    db: None,
) -> None:
    # Given
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Basic not-base64!!")
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(url, data={"action": "members"}, format="json")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_mixpanel_webhook__unknown_key_in_basic_password__returns_401(
    db: None,
) -> None:
    # Given
    client = _basic_auth_client("not-a-key")
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(url, data={"action": "members"}, format="json")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_mixpanel_webhook__distinct_id_over_1024_bytes__returns_400_failure(
    postgres_cohort_sync_key: _KeyAndPlaintext,
    mixpanel_cohort: Cohort,
) -> None:
    # Given - 512 three-byte characters: few characters, too many bytes
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "add_members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": "€" * 512}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["status"] == "failure"
    assert "1024 bytes" in body["error"]["message"]
    assert not CohortMembership.objects.exists()


def test_mixpanel_webhook__over_1000_members__returns_400_failure(
    postgres_cohort_sync_key: _KeyAndPlaintext,
    mixpanel_cohort: Cohort,
) -> None:
    # Given - one more member than Mixpanel's documented batch size
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "add_members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": f"user-{i}"} for i in range(1001)],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["status"] == "failure"
    assert not CohortMembership.objects.exists()


def test_mixpanel_webhook__members_action_at_segment_limit__returns_400_failure(
    postgres_cohort_sync_key: _KeyAndPlaintext,
    settings: SettingsWrapper,
) -> None:
    # Given - the project already holds as many segments as the plan allows
    key, plaintext = postgres_cohort_sync_key
    project = key.environment.project
    settings.EDGE_ENABLED = True
    project.max_segments_allowed = 1
    project.save()
    Segment.objects.create(name="existing", project=project)
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "members",
            "parameters": {
                "mixpanel_cohort_id": "mp-99",
                "mixpanel_cohort_name": "New cohort",
                "members": [{"mixpanel_distinct_id": "user-1"}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body["action"] == "members"
    assert body["status"] == "failure"
    assert "maximum allowed segments" in body["error"]["message"]
    assert not Cohort.objects.filter(external_id="mp-99").exists()


def test_mixpanel_webhook__members_action_while_cohort_draining__returns_404_failure(
    postgres_cohort_sync_key: _KeyAndPlaintext,
    mixpanel_cohort: Cohort,
) -> None:
    # Given - the cohort was deleted in Flagsmith and is still draining
    mixpanel_cohort.deletion_requested_at = timezone.now()
    mixpanel_cohort.save()
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": "user-1"}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {
        "action": "members",
        "status": "failure",
        "error": {"message": "Cohort is being deleted.", "code": 404},
    }
    assert Cohort.objects.filter(source_type=CohortSourceType.MIXPANEL).count() == 1


@pytest.mark.saas_mode
def test_mixpanel_webhook__saas_free_plan__returns_403(
    postgres_cohort_sync_key: _KeyAndPlaintext,
) -> None:
    # Given
    _, plaintext = postgres_cohort_sync_key
    client = _basic_auth_client(plaintext)
    url = reverse("api-v1:cohort-sync:mixpanel")

    # When
    response = client.post(
        url,
        data={
            "action": "members",
            "parameters": {
                "mixpanel_cohort_id": "mp-42",
                "mixpanel_cohort_name": "Power users",
                "members": [{"mixpanel_distinct_id": "user-1"}],
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_webhook_add_members__csv_cohort__applies_memberships(
    cohort: Cohort,
) -> None:
    # Given
    _, plaintext = CohortSyncKey.objects.create_key(
        name="test key", environment=cohort.environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:webhook-add", kwargs={"pk": str(cohort.uuid)})

    # When
    response = client.post(
        url, data={"identifiers": ["user-1", "user-2"]}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert sorted(
        CohortMembership.objects.filter(cohort=cohort).values_list(
            "identifier", "state"
        )
    ) == [
        ("user-1", CohortMembershipState.APPLIED),
        ("user-2", CohortMembershipState.APPLIED),
    ]
    identity = Identity.objects.get(environment=cohort.environment, identifier="user-1")
    assert identity.system_traits == {cohort.system_trait_key: True}


def test_webhook_remove_members__applied_member__removes_membership_and_trait(
    cohort: Cohort,
) -> None:
    # Given
    Identity.objects.create(
        environment=cohort.environment,
        identifier="member",
        system_traits={cohort.system_trait_key: True},
    )
    CohortMembership.objects.create(
        cohort=cohort, identifier="member", state=CohortMembershipState.APPLIED
    )
    _, plaintext = CohortSyncKey.objects.create_key(
        name="test key", environment=cohort.environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:webhook-remove", kwargs={"pk": str(cohort.uuid)})

    # When
    response = client.post(url, data={"identifiers": ["member"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert not CohortMembership.objects.filter(cohort=cohort).exists()
    identity = Identity.objects.get(environment=cohort.environment, identifier="member")
    assert identity.system_traits == {}


def test_webhook_add_members__non_csv_cohort__returns_404(
    cohort_sync_key: _KeyAndPlaintext,
    amplitude_cohort: Cohort,
) -> None:
    # Given
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse(
        "api-v1:cohort-sync:webhook-add", kwargs={"pk": str(amplitude_cohort.uuid)}
    )

    # When
    response = client.post(url, data={"identifiers": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_webhook_add_members__other_environment_key__returns_404(
    cohort: Cohort,
) -> None:
    # Given - a key scoped to a different environment than the cohort's
    other_environment = Environment.objects.create(
        name="Other environment", project=cohort.environment.project
    )
    _, plaintext = CohortSyncKey.objects.create_key(
        name="other key", environment=other_environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:webhook-add", kwargs={"pk": str(cohort.uuid)})

    # When
    response = client.post(url, data={"identifiers": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert not CohortMembership.objects.exists()


def test_webhook_add_members__identifier_over_1024_bytes__returns_400(
    cohort: Cohort,
) -> None:
    # Given - 512 three-byte characters: few characters, too many bytes
    multibyte_identifier = "€" * 512
    _, plaintext = CohortSyncKey.objects.create_key(
        name="test key", environment=cohort.environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:webhook-add", kwargs={"pk": str(cohort.uuid)})

    # When
    response = client.post(
        url, data={"identifiers": [multibyte_identifier]}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "1024 bytes" in str(response.json())
    assert not CohortMembership.objects.exists()


def test_webhook_add_members__over_10000_identifiers__returns_400(
    cohort: Cohort,
) -> None:
    # Given
    _, plaintext = CohortSyncKey.objects.create_key(
        name="test key", environment=cohort.environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:webhook-add", kwargs={"pk": str(cohort.uuid)})

    # When
    response = client.post(
        url,
        data={"identifiers": [f"user-{i}" for i in range(10001)]},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not CohortMembership.objects.exists()


def test_webhook_add_members__empty_identifiers__returns_400(
    cohort: Cohort,
) -> None:
    # Given
    _, plaintext = CohortSyncKey.objects.create_key(
        name="test key", environment=cohort.environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:webhook-add", kwargs={"pk": str(cohort.uuid)})

    # When
    response = client.post(url, data={"identifiers": []}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_webhook_add_members__malformed_uuid__returns_404(
    cohort: Cohort,
) -> None:
    # Given
    _, plaintext = CohortSyncKey.objects.create_key(
        name="test key", environment=cohort.environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:webhook-add", kwargs={"pk": "not-a-uuid"})

    # When
    response = client.post(url, data={"identifiers": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_webhook_add_members__deletion_requested_cohort__returns_404(
    cohort: Cohort,
) -> None:
    # Given
    cohort.deletion_requested_at = timezone.now()
    cohort.save()
    _, plaintext = CohortSyncKey.objects.create_key(
        name="test key", environment=cohort.environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:webhook-add", kwargs={"pk": str(cohort.uuid)})

    # When
    response = client.post(url, data={"identifiers": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_webhook_add_members__missing_credentials__returns_401(
    cohort: Cohort,
) -> None:
    # Given
    url = reverse("api-v1:cohort-sync:webhook-add", kwargs={"pk": str(cohort.uuid)})

    # When
    response = APIClient().post(url, data={"identifiers": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.saas_mode
def test_webhook_add_members__saas_free_plan__returns_403(
    cohort: Cohort,
) -> None:
    # Given
    _, plaintext = CohortSyncKey.objects.create_key(
        name="test key", environment=cohort.environment
    )
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:webhook-add", kwargs={"pk": str(cohort.uuid)})

    # When
    response = client.post(url, data={"identifiers": ["user-1"]}, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_amplitude_create_list__shape_param__returns_only_that_shape(
    cohort_sync_key: _KeyAndPlaintext,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    _, plaintext = cohort_sync_key
    client = _authenticated_client(plaintext)
    url = reverse("api-v1:cohort-sync:amplitude-list")

    # When
    response = client.post(
        f"{url}?shape=nested_camel", data={"name": "Beta users"}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    cohort = Cohort.objects.get(source_type=CohortSourceType.AMPLITUDE)
    assert response.json() == {"response": {"listId": str(cohort.uuid)}}
