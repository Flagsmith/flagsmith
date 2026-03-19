import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from integrations.rudderstack.models import RudderstackConfiguration


def test_create_rudderstack_config__valid_data__returns_201(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    data = {"api_key": "abc-123"}

    url = reverse(
        "api-v1:environments:integrations-rudderstack-list",
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
    assert RudderstackConfiguration.objects.filter(environment=environment).count() == 1


def test_create_rudderstack_config__duplicate_config__returns_400(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = RudderstackConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    url = reverse(
        "api-v1:environments:integrations-rudderstack-list",
        args=[environment.api_key],
    )
    data = {"api_key": config.api_key}

    # When
    response = admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert RudderstackConfiguration.objects.filter(environment=environment).count() == 1


def test_update_rudderstack_config__valid_data__returns_200(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = RudderstackConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    api_key_updated = "new api"
    data = {"api_key": api_key_updated}

    # When
    url = reverse(
        "api-v1:environments:integrations-rudderstack-detail",
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


def test_list_rudderstack_config__existing_config__returns_200(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = RudderstackConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    url = reverse(
        "api-v1:environments:integrations-rudderstack-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data == [
        {
            "api_key": config.api_key,
            "base_url": config.base_url,
            "id": config.id,
        }
    ]


def test_delete_rudderstack_config__existing_config__returns_204(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = RudderstackConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    # When
    url = reverse(
        "api-v1:environments:integrations-rudderstack-detail",
        args=[environment.api_key, config.id],
    )
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not RudderstackConfiguration.objects.filter(environment=environment).exists()
