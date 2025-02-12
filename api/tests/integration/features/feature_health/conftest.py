import json

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def sample_feature_health_provider_webhook_url(
    project: int, admin_client_new: APIClient
) -> str:
    feature_health_provider_data = {"name": "Sample"}
    url = reverse("api-v1:projects:feature-health-providers-list", args=[project])
    response = admin_client_new.post(url, data=feature_health_provider_data)
    return response.json()["webhook_url"]


@pytest.fixture
def unhealthy_feature(
    sample_feature_health_provider_webhook_url: str,
    feature_name: str,
    feature: int,
    api_client: APIClient,
) -> int:
    api_client.post(
        sample_feature_health_provider_webhook_url,
        data=json.dumps({"feature": feature_name, "status": "unhealthy"}),
        content_type="application/json",
    )
    return feature
