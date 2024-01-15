import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from integrations.mixpanel.models import MixpanelConfiguration


def test_should_create_mixpanel_config_when_post(
    admin_client: APIClient,
    environment: Environment,
):
    # Given
    data = {"api_key": "abc-123"}
    url = reverse(
        "api-v1:environments:integrations-mixpanel-list",
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
    assert MixpanelConfiguration.objects.filter(environment=environment).count() == 1


def test_should_return_400_when_duplicate_mixpanel_config_is_posted(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = MixpanelConfiguration.objects.create(
        api_key="api_123", environment=environment
    )
    data = {"api_key": config.api_key}
    url = reverse(
        "api-v1:environments:integrations-mixpanel-list",
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
    assert MixpanelConfiguration.objects.filter(environment=environment).count() == 1


def test_should_update_configuration_when_put(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = MixpanelConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    api_key_updated = "new api"
    data = {"api_key": api_key_updated}
    url = reverse(
        "api-v1:environments:integrations-mixpanel-detail",
        args=[environment.api_key, config.id],
    )

    # When
    response = admin_client.put(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )
    config.refresh_from_db()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert config.api_key == api_key_updated


def test_should_return_mixpanel_config_list_when_requested(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = MixpanelConfiguration.objects.create(
        api_key="api_123", environment=environment
    )
    url = reverse(
        "api-v1:environments:integrations-mixpanel-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    expected_response = {"api_key": config.api_key, "id": config.id}
    assert response.data == [expected_response]


def test_should_remove_configuration_when_delete(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = MixpanelConfiguration.objects.create(
        api_key="api_123", environment=environment
    )
    url = reverse(
        "api-v1:environments:integrations-mixpanel-detail",
        args=[environment.api_key, config.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not MixpanelConfiguration.objects.filter(environment=environment).exists()
