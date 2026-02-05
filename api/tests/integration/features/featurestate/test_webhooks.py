import json

import pytest
import responses
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from rest_framework import status
from rest_framework.test import APIClient

WEBHOOK_URL = "https://example.com/webhook"


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
    webhook: str,
) -> None:
    """
    Test for issue #6190: Webhook payloads do not include multivariate values.

    When updating the percentage allocation of a multivariate option,
    the webhook payload should include the multivariate_feature_state_values
    with their percentage allocations.
    """
    # Given
    responses.add(responses.POST, webhook, status=200)

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

    # When - update only the multivariate percentage allocation
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
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Verify webhook was called
    assert len(responses.calls) >= 1
    webhook_payload = json.loads(responses.calls[0].request.body)["data"]  # type: ignore[union-attr]

    # Verify the payload includes multivariate values
    # This currently fails - issue #6190
    assert "multivariate_feature_state_values" in webhook_payload["new_state"]
    assert "multivariate_feature_state_values" in webhook_payload["previous_state"]

    new_mv_values = webhook_payload["new_state"]["multivariate_feature_state_values"]
    previous_mv_values = webhook_payload["previous_state"][
        "multivariate_feature_state_values"
    ]

    assert len(new_mv_values) == 1
    assert len(previous_mv_values) == 1
    assert new_mv_values[0]["percentage_allocation"] == new_percentage
    assert previous_mv_values[0]["percentage_allocation"] == old_percentage
