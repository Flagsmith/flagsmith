import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from integrations.dynatrace.models import DynatraceConfiguration


def test_should_create_dynatrace_config_when_post(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given setup data
    data = {
        "base_url": "http://test.com",
        "api_key": "abc-123",
        "entity_selector": "type(APPLICATION),entityName(docs)",
    }
    url = reverse(
        "api-v1:environments:integrations-dynatrace-list",
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
    # and
    assert DynatraceConfiguration.objects.filter(environment=environment).count() == 1


def test_should_return_400_when_duplicate_dynatrace_config_is_posted(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    DynatraceConfiguration.objects.create(
        base_url="http://test.com", api_key="api_123", environment=environment
    )
    data = {
        "base_url": "http://test.com",
        "api_key": "abc-123",
        "entity_selector": "type(APPLICATION),entityName(docs)",
    }
    url = reverse(
        "api-v1:environments:integrations-dynatrace-list",
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
    assert DynatraceConfiguration.objects.filter(environment=environment).count() == 1


def test_should_update_configuration_when_put(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = DynatraceConfiguration.objects.create(
        base_url="http://test.com", api_key="api_123", environment=environment
    )
    api_key_updated = "new api"
    data = {
        "base_url": "http://test.com",
        "api_key": "new api",
        "entity_selector": "type(APPLICATION),entityName(docs)",
    }

    # When
    url = reverse(
        "api-v1:environments:integrations-dynatrace-detail",
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


def test_should_return_dynatrace_config_list_when_requested(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = DynatraceConfiguration.objects.create(
        base_url="http://test.com", api_key="api_123", environment=environment
    )
    url = reverse(
        "api-v1:environments:integrations-dynatrace-list",
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
            "entity_selector": "",
            "id": config.id,
        }
    ]


def test_should_remove_configuration_when_delete(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = DynatraceConfiguration.objects.create(
        base_url="http://test.com", api_key="api_123", environment=environment
    )
    # When
    url = reverse(
        "api-v1:environments:integrations-dynatrace-detail",
        args=[environment.api_key, config.id],
    )
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not DynatraceConfiguration.objects.filter(environment=environment).exists()
