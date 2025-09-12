import json
from datetime import datetime

import pytest
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog
from core.signals import create_audit_log_from_historical_record
from features.models import FeatureState
from features.workflows.core.models import ChangeRequest
from organisations.subscriptions.metadata import BaseSubscriptionMetadata
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


def test_get_audit_logs_makes_expected_queries(  # type: ignore[no-untyped-def]
    admin_client,
    project,
    environment,
    feature,
    feature_state,
    django_assert_num_queries,
):
    url = reverse("api-v1:audit-list")

    with django_assert_num_queries(3):
        res = admin_client.get(url, {"project": project})

    assert res.status_code == status.HTTP_200_OK
    assert res.json()["count"] == 3


def test_retrieve_audit_log_for_environment_change(
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
    retrieve_response_json = retrieve_response.json()
    assert len(retrieve_response_json["change_details"]) == 1
    assert retrieve_response_json["change_details"][0]["field"] == "name"
    assert retrieve_response_json["change_details"][0]["new"] == new_name
    assert retrieve_response_json["change_details"][0]["old"] == environment_name


def test_retrieve_audit_log_for_feature_state_enabled_change(
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


def test_creates_audit_log_for_feature_state_update(
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
def test_creates_audit_log_for_scheduled_feature_state_update(
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


def test_retrieve_audit_log_for_feature_state_value_change(
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


def test_retrieve_audit_log_does_not_include_change_details_for_non_update(
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


def test_retrieve_audit_log_includes_changes_when_segment_override_created_and_deleted_for_enabled_state(
    admin_client: APIClient,
    project: int,
    feature: int,
    environment_api_key: str,
    environment: int,
    segment: int,
) -> None:
    # First, let's create a segment override
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

    # Now, that should have created an audit log, let's check
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

    # now let's check that we have some information about the change
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


def test_retrieve_audit_log_includes_changes_when_segment_override_created_for_feature_value(
    admin_client: APIClient,
    project: int,
    feature: int,
    default_feature_value: str,
    environment_api_key: str,
    environment: int,
    segment: int,
) -> None:
    # First, let's create a segment override
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

    # Now, that should have created an audit log, let's check
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

    # now let's check that we have some information about the change
    # This is treated as an update since the FeatureStateValue is created
    # automatically when the FeatureState is created, and then updated
    # with the value in the request.
    assert audit_log_details["change_type"] == "UPDATE"
    assert audit_log_details["change_details"] == [
        {"field": "string_value", "old": "default_value", "new": "foo"},
    ]
