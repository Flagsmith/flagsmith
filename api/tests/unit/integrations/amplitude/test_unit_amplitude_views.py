import json

from django.urls import reverse
from rest_framework import status


def test_create_amplitude_integration(environment, admin_client):
    # Given
    url = reverse(
        "api-v1:environments:integrations-amplitude-list", args=[environment.api_key]
    )

    # When
    response = admin_client.post(
        path=url,
        data=json.dumps({"api_key": "some-key"}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_create_amplitude_integration_in_environment_with_deleted_integration(
    environment, admin_client, deleted_amplitude_integration
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-amplitude-list", args=[environment.api_key]
    )

    # When
    response = admin_client.post(
        path=url,
        data=json.dumps({"api_key": "some-key"}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
