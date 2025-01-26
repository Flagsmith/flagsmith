import json

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_webhook__post__expected_feature_health_event_created__expected_tag_added(
    feature: int,
    project: int,
    feature_name: str,
    sample_feature_health_provider_webhook_url: str,
    api_client: APIClient,
    admin_client: APIClient,
) -> None:
    # Given
    feature_health_events_url = reverse(
        "api-v1:projects:feature-health-events-list", args=[project]
    )
    tags_url = reverse("api-v1:projects:tags-list", args=[project])
    features_url = reverse("api-v1:projects:project-features-list", args=[project])

    # When
    webhook_data = {
        "feature": feature_name,
        "status": "unhealthy",
    }
    api_client.post(
        sample_feature_health_provider_webhook_url,
        data=json.dumps(webhook_data),
        content_type="application/json",
    )

    # Then
    response = admin_client.get(feature_health_events_url)
    assert response.status_code == 200
    assert response.json() == [
        {
            "created_at": "2023-01-19T09:09:47.325132Z",
            "environment": None,
            "feature": feature,
            "provider_name": "Sample",
            "reason": "",
            "type": "UNHEALTHY",
        }
    ]
    response = admin_client.get(tags_url)
    assert (
        tag_data := next(
            tag_data
            for tag_data in response.json()["results"]
            if tag_data.get("label") == "Unhealthy"
        )
    )
    response = admin_client.get(features_url)
    feature_data = next(
        feature_data
        for feature_data in response.json()["results"]
        if feature_data.get("id") == feature
    )
    assert tag_data["id"] in feature_data["tags"]
