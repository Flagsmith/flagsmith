import json
from datetime import UTC, datetime, timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from freezegun.api import FrozenDateTimeFactory
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from core.signals import create_audit_log_from_historical_record
from features.future.types import UpdateFlagRequest
from features.models import Feature, FeatureState
from features.workflows.core.models import ChangeRequest
from organisations.subscriptions.metadata import BaseSubscriptionMetadata
from tests.types import CreateSegmentOverrideFixture, ScheduleFlagChangeFixture
from users.models import FFAdminUser


@pytest.fixture(autouse=True)
def _subscription_metadata(mocker: MockerFixture) -> None:
    metadata = BaseSubscriptionMetadata(
        audit_log_visibility_days=None,
    )
    mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
        return_value=metadata,
    )


def test_list_audit_logs__with_project_filter__makes_expected_queries(  # type: ignore[no-untyped-def]
    admin_client,
    project,
    environment,
    feature,
    feature_state,
    django_assert_num_queries,
):
    # Given
    url = reverse("api-v1:audit-list")

    # When
    with django_assert_num_queries(3):
        res = admin_client.get(url, {"project": project})

    # Then
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["count"] == 3


def test_retrieve_audit_log__environment_change__includes_change_details(
    admin_client: APIClient,
    project: int,
    environment_api_key: str,
    environment_name: str,
    environment: int,
) -> None:
    # Given
    # we update the environment
    update_environment_url = reverse(
        "api-v1:environments:environment-detail",
        args=[environment_api_key],
    )
    new_name = "some new name!"
    data = {"name": new_name}
    admin_client.patch(
        update_environment_url, data=json.dumps(data), content_type="application/json"
    )

    # we list the audit log to get an audit record that was created when we update the feature above
    list_audit_log_url = reverse("api-v1:audit-list")
    list_response = admin_client.get(list_audit_log_url)

    # When
    # We retrieve the record directly where we updated the environment
    environment_update_result = next(
        filter(
            lambda r: r["log"].startswith("Environment updated"),
            list_response.json()["results"],
        )
    )
    retrieve_audit_log_url = reverse(
        "api-v1:audit-detail", args=[environment_update_result["id"]]
    )
    retrieve_response = admin_client.get(retrieve_audit_log_url)

    # Then
    retrieve_response_json = retrieve_response.json()
    assert len(retrieve_response_json["change_details"]) == 1
    assert retrieve_response_json["change_details"][0]["field"] == "name"
    assert retrieve_response_json["change_details"][0]["new"] == new_name
    assert retrieve_response_json["change_details"][0]["old"] == environment_name


def test_retrieve_audit_log__feature_state_enabled_change__includes_change_details(
    admin_client: APIClient,
    environment_api_key: str,
    environment: int,
    feature: int,
    feature_state: int,
) -> None:
    # Given
    # we update the state and value of a feature in an environment
    update_feature_state_url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment_api_key, feature_state],
    )
    data = {"enabled": True}
    admin_client.patch(
        update_feature_state_url, data=json.dumps(data), content_type="application/json"
    )

    # we list the audit log to get an audit record that was created when we update the feature above
    list_audit_log_url = reverse("api-v1:audit-list")
    list_response = admin_client.get(list_audit_log_url)
    list_results = list_response.json()["results"]

    # When
    # We retrieve the records directly where we updated the feature state
    flag_state_update_result = next(
        filter(
            lambda r: r["log"].startswith("Flag state updated"),
            list_results,
        )
    )
    retrieve_audit_log_url = reverse(
        "api-v1:audit-detail", args=[flag_state_update_result["id"]]
    )
    retrieve_response = admin_client.get(retrieve_audit_log_url)

    # Then
    retrieve_response_json = retrieve_response.json()
    assert len(retrieve_response_json["change_details"]) == 1
    assert retrieve_response_json["change_details"][0]["field"] == "enabled"
    assert retrieve_response_json["change_details"][0]["new"] is True
    assert retrieve_response_json["change_details"][0]["old"] is False


def test_create_audit_log_from_historical_record__feature_state_update__creates_correct_log(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    environment_api_key: str,
    environment: int,
    feature_state: int,
    feature: int,
) -> None:
    # Given
    feature_state_obj = FeatureState.objects.get(pk=feature_state)
    feature_state_obj.enabled = True
    feature_state_obj.save()
    history_instance = feature_state_obj.history.first()
    assert history_instance.history_type == "~"

    # When
    create_audit_log_from_historical_record(
        instance=feature_state_obj,
        history_user=admin_user,
        history_instance=history_instance,
    )

    # Then
    audit_log = AuditLog.objects.first()
    feature_name = feature_state_obj.feature.name
    assert audit_log.log == f"Flag state updated for feature: {feature_name}"


# Future people please bump this up when it's due
@freeze_time("2199-04-14T12:30:00+00:00")
@pytest.mark.parametrize(
    "tz_name, django_datetime_format, expected_ts",
    [
        ("America/Los_Angeles", "Y-m-d H:i (T)", "2199-04-15 05:30 (PDT)"),
        ("UTC", "D j M Y H:i (T)", "Mon 15 Apr 2199 12:30 (UTC)"),
        ("Asia/Tokyo", "Y年n月j日 H:i (T)", "2199年4月15日 21:30 (JST)"),
    ],
)
def test_create_audit_log_from_historical_record__scheduled_feature_state__includes_schedule_time(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    django_datetime_format: str,
    environment_api_key: str,
    environment: int,
    expected_ts: str,
    feature_state: int,
    feature: int,
    settings: SettingsWrapper,
    tz_name: str,
) -> None:
    # Given
    settings.DATETIME_FORMAT = django_datetime_format
    settings.TIME_ZONE = tz_name
    future = datetime.fromisoformat("2199-04-15T12:30:00+00:00")
    change_request = ChangeRequest.objects.create(
        environment_id=environment,
        title="Test",
        committed_at=timezone.now(),
        committed_by=admin_user,
    )
    feature_state_obj = FeatureState.objects.get(pk=feature_state)
    feature_state_obj.change_request = change_request
    feature_state_obj.enabled = True
    feature_state_obj.live_from = future
    feature_state_obj.save()
    history_instance = feature_state_obj.history.first()
    assert history_instance.history_type == "~"

    # When
    create_audit_log_from_historical_record(
        instance=feature_state_obj,
        history_user=admin_user,
        history_instance=history_instance,
    )

    # Then
    audit_log = AuditLog.objects.first()
    feature_name = feature_state_obj.feature.name
    assert (
        audit_log.log
        == f"Flag state for feature '{feature_name}' scheduled for update by Change Request '{change_request.title}' at {expected_ts}."
    )


def test_retrieve_audit_log__feature_state_value_change__includes_change_details(
    admin_client: APIClient,
    environment_api_key: str,
    environment: int,
    feature: int,
    feature_state: int,
    default_feature_value: str,
) -> None:
    # Given
    # we update the state and value of a feature in an environment
    new_value = "foobar"
    update_feature_state_url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment_api_key, feature_state],
    )
    data = {"feature_state_value": new_value}
    admin_client.patch(
        update_feature_state_url, data=json.dumps(data), content_type="application/json"
    )

    # we list the audit log to get an audit record that was created when we update the feature above
    list_audit_log_url = reverse("api-v1:audit-list")
    list_response = admin_client.get(list_audit_log_url)
    list_results = list_response.json()["results"]

    # When
    # We retrieve the records directly where we updated the feature state
    flag_state_update_result = next(
        filter(
            lambda r: r["log"].startswith("Remote config value updated"),
            list_results,
        )
    )
    retrieve_audit_log_url = reverse(
        "api-v1:audit-detail", args=[flag_state_update_result["id"]]
    )
    retrieve_response = admin_client.get(retrieve_audit_log_url)

    # Then
    retrieve_response_json = retrieve_response.json()
    assert len(retrieve_response_json["change_details"]) == 1
    assert retrieve_response_json["change_details"][0]["field"] == "string_value"
    assert retrieve_response_json["change_details"][0]["new"] == new_value
    assert retrieve_response_json["change_details"][0]["old"] == default_feature_value


def test_retrieve_audit_log__non_update_record__returns_empty_change_details(
    admin_client: APIClient, project: int, environment: str
) -> None:
    # Given
    # we list the audit log to get an audit record that was created when
    # the environment was created in the fixture
    list_audit_log_url = reverse("api-v1:audit-list")
    list_response = admin_client.get(list_audit_log_url)

    environment_update_result = next(
        filter(
            lambda r: r["log"].startswith("New Environment created"),
            list_response.json()["results"],
        )
    )

    # When
    retrieve_audit_log_url = reverse(
        "api-v1:audit-detail", args=[environment_update_result["id"]]
    )
    retrieve_response = admin_client.get(retrieve_audit_log_url)

    # Then
    assert retrieve_response.json()["change_details"] == []


def test_retrieve_audit_log__segment_override_created_and_deleted__includes_change_details(
    admin_client: APIClient,
    project: int,
    feature: int,
    environment_api_key: str,
    environment: int,
    segment: int,
) -> None:
    # Given - create a segment override
    data = {
        "feature_segment": {"segment": segment},
        "enabled": True,
        "feature_state_value": {},
    }
    create_segment_override_url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment_api_key, feature],
    )
    create_segment_override_response = admin_client.post(
        create_segment_override_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert create_segment_override_response.status_code == status.HTTP_201_CREATED
    segment_override_feature_segment_id = create_segment_override_response.json()[
        "feature_segment"
    ]["id"]

    # When - retrieve the audit log for the creation
    get_audit_logs_url = "%s?environment=%s" % (
        reverse("api-v1:audit-list"),
        environment,
    )
    get_audit_logs_response = admin_client.get(get_audit_logs_url)
    assert get_audit_logs_response.status_code == status.HTTP_200_OK
    results = get_audit_logs_response.json()["results"]

    # the first audit log in the list (i.e. most recent) should be the one that we want
    audit_log_id = results[0]["id"]
    get_create_override_audit_log_detail_url = reverse(
        "api-v1:audit-detail", args=[audit_log_id]
    )
    get_create_override_audit_log_detail_response = admin_client.get(
        get_create_override_audit_log_detail_url
    )
    assert (
        get_create_override_audit_log_detail_response.status_code == status.HTTP_200_OK
    )
    create_override_audit_log_details = (
        get_create_override_audit_log_detail_response.json()
    )

    # Then - the creation audit log has the expected change details
    assert create_override_audit_log_details["change_type"] == "CREATE"
    assert create_override_audit_log_details["change_details"] == [
        {"field": "enabled", "old": None, "new": True},
    ]

    # now let's delete the segment override
    delete_segment_override_url = reverse(
        "api-v1:features:feature-segment-detail",
        args=[segment_override_feature_segment_id],
    )
    response = admin_client.delete(delete_segment_override_url)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # now we should have one more audit log record
    get_audit_logs_response_2 = admin_client.get(get_audit_logs_url)
    assert get_audit_logs_response_2.status_code == status.HTTP_200_OK
    results = get_audit_logs_response_2.json()["results"]
    assert len(results) == 5

    # and the first one in the list should be for the deletion of the segment override
    delete_override_audit_log_id = results[0]["id"]
    get_delete_override_audit_log_detail_url = reverse(
        "api-v1:audit-detail", args=[delete_override_audit_log_id]
    )
    get_delete_override_audit_log_detail_response = admin_client.get(
        get_delete_override_audit_log_detail_url
    )
    assert (
        get_delete_override_audit_log_detail_response.status_code == status.HTTP_200_OK
    )
    delete_override_audit_log_details = (
        get_delete_override_audit_log_detail_response.json()
    )

    # now let's check that we have some information about the change
    assert delete_override_audit_log_details["change_type"] == "DELETE"
    assert delete_override_audit_log_details["change_details"] == []


def test_retrieve_audit_log__segment_override_created_for_feature_value__includes_change_details(
    admin_client: APIClient,
    project: int,
    feature: int,
    default_feature_value: str,
    environment_api_key: str,
    environment: int,
    segment: int,
) -> None:
    # Given - create a segment override with a feature value
    data = {
        "feature_segment": {"segment": segment},
        "feature_state_value": {"value_type": "unicode", "string_value": "foo"},
    }
    create_segment_override_url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment_api_key, feature],
    )
    create_segment_override_response = admin_client.post(
        create_segment_override_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert create_segment_override_response.status_code == status.HTTP_201_CREATED

    # When - retrieve the audit log detail
    get_audit_logs_url = "%s?environment=%s" % (
        reverse("api-v1:audit-list"),
        environment,
    )
    get_audit_logs_response = admin_client.get(get_audit_logs_url)
    assert get_audit_logs_response.status_code == status.HTTP_200_OK
    results = get_audit_logs_response.json()["results"]

    # and we should only have one audit log in the list related to the segment override
    # (since the FeatureState hasn't changed)
    # 1 for creating the feature + 1 for creating the environment + 1 for creating the segment
    # + 1 for the segment override = 4
    assert len(results) == 4

    # the first audit log in the list (i.e. most recent) should be the one that we want
    audit_log_id = results[0]["id"]
    get_audit_log_detail_url = reverse("api-v1:audit-detail", args=[audit_log_id])
    get_audit_log_detail_response = admin_client.get(get_audit_log_detail_url)
    assert get_audit_log_detail_response.status_code == status.HTTP_200_OK
    audit_log_details = get_audit_log_detail_response.json()

    # Then - the audit log contains the expected change details
    # This is treated as an update since the FeatureStateValue is created
    # automatically when the FeatureState is created, and then updated
    # with the value in the request.
    assert audit_log_details["change_type"] == "UPDATE"
    assert audit_log_details["change_details"] == [
        {"field": "string_value", "old": "default_value", "new": "foo"},
    ]


@pytest.mark.freeze_time("2026-10-06T09:00:00Z")
@pytest.mark.skipif(
    not settings.WORKFLOWS_LOGIC_INSTALLED,
    reason="workflows_logic module not installed (private package extra)",
)
def test_list_audit_logs__segment_override_differs_from_flag_edited_while_change_was_scheduled__lists_override_created_once(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    project: int,
    segment: int,
    segment_name: str,
    freezer: FrozenDateTimeFactory,
    schedule_flag_change: ScheduleFlagChangeFixture,
    create_segment_override: CreateSegmentOverrideFixture,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    tomorrow = datetime.now(tz=UTC) + timedelta(days=1)
    freezer.tick(timedelta(minutes=1))
    admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{checkout.id}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )
    freezer.tick(timedelta(minutes=1))
    schedule_flag_change(feature_id=checkout.id, enabled=False, live_from=tomorrow)
    freezer.tick(timedelta(minutes=1))
    schedule_flag_change(
        feature_id=checkout.id, enabled=True, live_from=datetime.now(tz=UTC)
    )
    freezer.move_to(tomorrow + timedelta(minutes=1))
    create_segment_override(environment_api_key, checkout.id, segment, enabled=True)

    # When
    response = admin_client.get("/api/v1/audit/", {"environment": environment})

    # Then
    assert response.status_code == 200
    assert [
        (audit_log["created_date"], audit_log["log"])
        for audit_log in response.json()["results"]
    ] == [
        (
            "2026-10-07T09:01:00Z",
            f"Flag state / Remote config value updated for feature 'checkout' and segment '{segment_name}'",
        ),
        (
            "2026-10-07T09:01:00Z",
            f"Remote config updated for segment override on feature 'checkout' and segment '{segment_name}'.",
        ),
        (
            "2026-10-06T09:03:00Z",
            "Change Request: Scheduled change created",
        ),
        (
            "2026-10-06T09:03:00Z",
            "Flag state / Remote config updated for feature: checkout by Change Request: Scheduled change",
        ),
        (
            "2026-10-06T09:02:00Z",
            "Change Request: Scheduled change created",
        ),
        (
            "2026-10-06T09:01:00Z",
            "Flag state updated for feature: checkout",
        ),
        (
            "2026-10-06T09:00:00Z",
            f"New Segment created: {segment_name}",
        ),
        (
            "2026-10-06T09:00:00Z",
            "New Environment created: Test Environment",
        ),
    ]
