import json

from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient


def test_update_segment_override__webhook_payload_has_correct_previous_and_new_values(
    admin_client: APIClient,
    environment: int,
    feature: int,
    segment: int,
    mocker: MockerFixture,
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

    # Mock call_environment_webhooks to capture the actual payload
    mock_call_environment_webhooks = mocker.patch(
        "features.tasks.call_environment_webhooks"
    )
    mocker.patch("features.tasks.call_organisation_webhooks")

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

    # Verify webhook was called
    mock_call_environment_webhooks.delay.assert_called_once()
    webhook_args = mock_call_environment_webhooks.delay.call_args.kwargs["args"]
    webhook_payload = webhook_args[1]  # (environment_id, data, event_type)

    # Verify the payload has correct values
    assert webhook_payload["new_state"]["feature_segment"] is not None
    assert webhook_payload["new_state"]["feature_state_value"] == new_value
    assert webhook_payload["previous_state"]["feature_state_value"] == old_value
