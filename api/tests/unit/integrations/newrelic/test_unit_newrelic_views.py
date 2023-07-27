import json

from django.urls import reverse
from rest_framework import status


def test_create_newrelic_configuration_in_project_with_deleted_configuration(
    admin_client, project, deleted_newrelic_configuration
):
    # Given
    url = reverse("api-v1:projects:integrations-new-relic-list", args=[project.id])

    api_key, base_url, app_id = "some-key", "https://api.newrelic.com/", "1"

    # When
    response = admin_client.post(
        path=url,
        data=json.dumps({"api_key": api_key, "base_url": base_url, "app_id": app_id}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert response_json["api_key"] == api_key
    assert response_json["base_url"] == base_url
    assert response_json["app_id"] == app_id
