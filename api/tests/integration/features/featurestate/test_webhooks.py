import json

import pytest
import responses
from django.urls import reverse
from freezegun import freeze_time
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from audit.tasks import create_feature_state_went_live_audit_log
from features.models import FeatureState
from features.workflows.core.models import ChangeRequest
from users.models import FFAdminUser

WEBHOOK_URL = "https://example.com/webhook"


def _extract_webhook_payloads(event_type: str | None):
    """Extract webhook payloads from responses cache"""
    return (
        payload
        for payload in (
            json.loads(r.request.body)
            for r in responses.calls
            if r.request.url == WEBHOOK_URL
        )
        if event_type is None or payload["event_type"] == event_type
    )


@pytest.fixture
def environment_webhook(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
) -> str:
    """Create an environment webhook via API and return its URL."""
    url = reverse(
        "api-v1:environments:environment-webhooks-list",
        args=[environment_api_key],
    )
    response = admin_client.post(url, data={"url": WEBHOOK_URL, "enabled": True})
    assert response.status_code == status.HTTP_201_CREATED
    return WEBHOOK_URL


@pytest.fixture
def organisation_webhook(
    admin_client: APIClient,
    organisation: int,
) -> str:
    """Create an organisation webhook via API and return its URL."""
    url = reverse(
        "api-v1:organisations:organisation-webhooks-list",
        args=[organisation],
    )
    response = admin_client.post(url, data={"url": WEBHOOK_URL, "enabled": True})
    assert response.status_code == status.HTTP_201_CREATED
    return WEBHOOK_URL


@responses.activate
def test_update_segment_override__webhook_payload_has_correct_previous_and_new_values(
    admin_client: APIClient,
    environment: int,
    feature: int,
    segment: int,
    environment_webhook: str,
) -> None:
    """
    Test for issue #6050: Webhook payload shows incorrect previous_state values
    when updating a segment override value via the API.

    The bug occurs because:
    1. The webhook signal fires on FeatureState.post_save
    2. drf-writable-nested saves the parent (FeatureState) before nested (FeatureStateValue)
    3. So the webhook captures stale values
    """
    # Given
    old_value = 0
    new_value = 1

    responses.add(responses.POST, environment_webhook, status=200)

    # First create a feature_segment
    feature_segment_url = reverse("api-v1:features:feature-segment-list")
    feature_segment_data = {
        "feature": feature,
        "segment": segment,
        "environment": environment,
    }
    feature_segment_response = admin_client.post(
        feature_segment_url,
        data=json.dumps(feature_segment_data),
        content_type="application/json",
    )
    assert feature_segment_response.status_code == status.HTTP_201_CREATED
    feature_segment_id = feature_segment_response.json()["id"]

    # Create segment override with initial value via API
    create_url = reverse("api-v1:features:featurestates-list")
    create_data = {
        "enabled": False,
        "feature_state_value": {"type": "int", "integer_value": old_value},
        "environment": environment,
        "feature": feature,
        "feature_segment": feature_segment_id,
    }
    create_response = admin_client.post(
        create_url, data=json.dumps(create_data), content_type="application/json"
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    segment_override_id = create_response.json()["id"]

    # Clear responses from create operation
    responses.calls.reset()

    # When - update the segment override via API
    url = reverse("api-v1:features:featurestates-detail", args=[segment_override_id])
    data = {
        "enabled": False,
        "feature_state_value": {"type": "int", "integer_value": new_value},
        "environment": environment,
        "feature": feature,
        "feature_segment": feature_segment_id,
    }
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Verify webhook was called with correct payload
    assert len(responses.calls) == 1
    webhook_payload = json.loads(responses.calls[0].request.body)["data"]  # type: ignore[union-attr]

    # Verify the payload has correct values
    assert webhook_payload["new_state"]["feature_segment"] is not None
    assert webhook_payload["new_state"]["feature_state_value"] == new_value
    assert webhook_payload["previous_state"]["feature_state_value"] == old_value


@pytest.mark.parametrize(
    "webhook",
    [lazy_fixture("environment_webhook"), lazy_fixture("organisation_webhook")],
)
@responses.activate
def test_update_multivariate_percentage__webhook_payload_includes_multivariate_values(
    admin_client: APIClient,
    environment: int,
    feature: int,
    mv_option_50_percent: int,
    mv_option_value: str,
    webhook: str,
    mocker: MockerFixture,
) -> None:
    """
    Test for issue #6190: Webhook payloads do not include multivariate values.

    When updating the percentage allocation of a multivariate option,
    the webhook payload should include the multivariate_feature_state_values
    with their percentage allocations.
    """
    # Given
    # Get the feature state for this environment
    feature_states_url = reverse("api-v1:features:featurestates-list")
    feature_states_response = admin_client.get(
        f"{feature_states_url}?environment={environment}&feature={feature}"
    )
    assert feature_states_response.status_code == status.HTTP_200_OK
    feature_state = feature_states_response.json()["results"][0]
    feature_state_id = feature_state["id"]

    # Get current multivariate feature state values
    assert len(feature_state["multivariate_feature_state_values"]) == 1
    mv_fs_value = feature_state["multivariate_feature_state_values"][0]
    old_percentage = mv_fs_value["percentage_allocation"]
    new_percentage = 75

    responses.add(responses.POST, webhook, status=200)

    # When
    # update only the multivariate percentage allocation
    url = reverse("api-v1:features:featurestates-detail", args=[feature_state_id])
    data = {
        "id": feature_state_id,
        "enabled": feature_state["enabled"],
        "feature_state_value": feature_state["feature_state_value"],
        "environment": environment,
        "feature": feature,
        "multivariate_feature_state_values": [
            {
                "id": mv_fs_value["id"],
                "multivariate_feature_option": mv_fs_value[
                    "multivariate_feature_option"
                ],
                "percentage_allocation": new_percentage,
            }
        ],
    }
    admin_client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    # `FLAG_UPDATED`` webhook was called
    # (should be the last sent event)
    last_call = responses.calls[-1]
    assert not isinstance(last_call, list)
    webhook_payload = json.loads(last_call.request.body)
    assert webhook_payload["event_type"] == "FLAG_UPDATED"

    # the payload includes multivariate values
    event_data = webhook_payload["data"]

    assert "multivariate_feature_state_values" in event_data["new_state"]
    assert "multivariate_feature_state_values" in event_data["previous_state"]

    assert event_data["new_state"]["multivariate_feature_state_values"] == [
        {
            "id": mocker.ANY,
            "multivariate_feature_option": {
                "id": mv_option_50_percent,
                "value": mv_option_value,
            },
            "percentage_allocation": new_percentage,
        },
    ]
    assert event_data["previous_state"]["multivariate_feature_state_values"] == [
        {
            "id": mocker.ANY,
            "multivariate_feature_option": {
                "id": mv_option_50_percent,
                "value": mv_option_value,
            },
            "percentage_allocation": old_percentage,
        },
    ]


@pytest.mark.parametrize(
    "webhook",
    [lazy_fixture("environment_webhook"), lazy_fixture("organisation_webhook")],
)
@responses.activate
def test_update_feature_live__legacy_versioning__webhook_payload_has_correct_previous_and_new_states(
    admin_client: APIClient,
    environment: int,
    feature: int,
    webhook: str,
):
    # Given
    feature_state_json = admin_client.get(
        f"/api/v1/features/featurestates/?environment={environment}&feature={feature}"
    ).json()["results"][0]
    feature_state_id = feature_state_json["id"]
    previous_state = feature_state_json["enabled"]
    previous_value = feature_state_json["feature_state_value"]["string_value"]

    # When
    responses.add(responses.POST, webhook, status=200)
    response = admin_client.put(
        f"/api/v1/features/featurestates/{feature_state_id}/",
        data={
            **feature_state_json,
            "feature_state_value": {"string_value": "new_value"},
            "enabled": True,
        },
        format="json",
    )
    assert response.status_code == 200

    # Then
    payload = list(_extract_webhook_payloads("FLAG_UPDATED"))[-1]
    assert payload["data"]["previous_state"]["enabled"] is previous_state
    assert payload["data"]["previous_state"]["feature_state_value"] == previous_value
    assert payload["data"]["new_state"]["enabled"] is True
    assert payload["data"]["new_state"]["feature_state_value"] == "new_value"


@pytest.mark.parametrize(
    "webhook",
    [lazy_fixture("environment_webhook"), lazy_fixture("organisation_webhook")],
)
@responses.activate
def test_update_feature_scheduled__legacy_versioning__webhook_payload_has_correct_previous_and_new_states(
    admin_user: FFAdminUser,
    environment: int,
    feature: int,
    webhook: str,
):
    """Covers https://github.com/Flagsmith/flagsmith/issues/2063"""
    # Given
    previous_feature_state = FeatureState.objects.get(feature_id=feature)
    previous_state = previous_feature_state.enabled
    previous_value = previous_feature_state.get_feature_state_value()

    # Simulate scheduled update in the frontend
    with freeze_time("2048-02-29T02:00:00+0000"):
        # POST create-change-request
        change_request = ChangeRequest.objects.create(
            environment=previous_feature_state.environment,
            title="Scheduled update",
            user=admin_user,
        )
        new_feature_state = FeatureState.objects.create(
            environment=previous_feature_state.environment,
            feature=previous_feature_state.feature,
            change_request=change_request,
            enabled=True,
            live_from="2048-02-29T06:00:00+0000",
            version=None,
        )
        new_feature_state.feature_state_value.string_value = "new_value"
        new_feature_state.feature_state_value.save()

    with freeze_time("2048-02-29T02:00:01+0000"):
        # PUT workflows:change-requests-detail pk={change_request.id}
        new_feature_state.save()
        new_feature_state.feature_state_value.save()

    responses.calls.reset()

    # When
    responses.add(responses.POST, webhook, status=200)
    change_request.commit(committed_by=admin_user)
    assert not any(_extract_webhook_payloads("FLAG_UPDATED"))
    with freeze_time("2048-02-29T06:00:00+0000"):
        create_feature_state_went_live_audit_log(new_feature_state.id)

    # Then
    payload = list(_extract_webhook_payloads("FLAG_UPDATED"))[-1]
    assert payload["data"]["previous_state"]["enabled"] is previous_state
    assert payload["data"]["previous_state"]["feature_state_value"] == previous_value
    assert payload["data"]["new_state"]["enabled"] is True
    assert payload["data"]["new_state"]["feature_state_value"] == "new_value"
