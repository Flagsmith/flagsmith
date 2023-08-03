import json

from django.urls import reverse
from rest_framework import status


def test_create_datadog_configuration_in_project_with_deleted_configuration(
    admin_client, project, deleted_datadog_configuration
):
    # Given
    url = reverse("api-v1:projects:integrations-datadog-list", args=[project.id])

    api_key, base_url = "some-key", "https://api.newrelic.com/"

    # When
    response = admin_client.post(
        path=url,
        data=json.dumps({"api_key": api_key, "base_url": base_url}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert response_json["api_key"] == api_key
    assert response_json["base_url"] == base_url
