import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from integrations.amplitude.models import AmplitudeConfiguration


def test_should_create_amplitude_config_when_post(
    admin_client: APIClient,
    environment: Environment,
):
    # Given
    data = {"api_key": "abc-123"}

    url = reverse(
        "api-v1:environments:integrations-amplitude-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert AmplitudeConfiguration.objects.filter(environment=environment).count() == 1


def test_should_return_400_when_duplicate_amplitude_config_is_posted(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = AmplitudeConfiguration.objects.create(
        api_key="api_123", environment=environment
    )
    data = {"api_key": config.api_key}

    url = reverse(
        "api-v1:environments:integrations-amplitude-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert AmplitudeConfiguration.objects.filter(environment=environment).count() == 1


def test_should_update_configuration_when_put(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = AmplitudeConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    api_key_updated = "new api"
    data = {"api_key": api_key_updated}

    # When
    url = reverse(
        "api-v1:environments:integrations-amplitude-detail",
        args=[environment.api_key, config.id],
    )
    response = admin_client.put(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    config.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert config.api_key == api_key_updated


def test_should_return_amplitude_config_list_when_requested(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = AmplitudeConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    url = reverse(
        "api-v1:environments:integrations-amplitude-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    expected_response = {
        "id": config.id,
        "api_key": config.api_key,
        "base_url": config.base_url,
    }

    assert response.data == [expected_response]


def test_should_remove_configuration_when_delete(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = AmplitudeConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    # When
    url = reverse(
        "api-v1:environments:integrations-amplitude-detail",
        args=[environment.api_key, config.id],
    )
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not AmplitudeConfiguration.objects.filter(environment=environment).exists()


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
