import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from integrations.segment.models import SegmentConfiguration


def test_should_create_segment_config_when_post(
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    data = {"api_key": "abc-123"}
    url = reverse(
        "api-v1:environments:integrations-segment-list",
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
    qs = SegmentConfiguration.objects.filter(environment=environment)
    assert qs.count() == 1
    assert response.data["id"] == qs.first().id


def test_should_return_400_when_duplicate_segment_config_is_posted(
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    config = SegmentConfiguration.objects.create(
        api_key="api_123", environment=environment
    )
    url = reverse(
        "api-v1:environments:integrations-segment-list",
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
    assert SegmentConfiguration.objects.filter(environment=environment).count() == 1


def test_should_update_configuration_when_put(
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    config = SegmentConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    api_key_updated = "new api"
    data = {"api_key": api_key_updated}
    url = reverse(
        "api-v1:environments:integrations-segment-detail",
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


def test_should_return_segment_config_list_when_requested(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:integrations-segment-list",
        args=[environment.api_key],
    )
    config = SegmentConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    # When
    response = admin_client.get(url)

    # Then
    expected_response = {"api_key": config.api_key, "id": config.id}
    assert response.status_code == status.HTTP_200_OK
    assert response.data == [expected_response]


def test_should_remove_configuration_when_delete(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    config = SegmentConfiguration.objects.create(
        api_key="api_123", environment=environment
    )

    # When
    url = reverse(
        "api-v1:environments:integrations-segment-detail",
        args=[environment.api_key, config.id],
    )
    res = admin_client.delete(url)

    # Then
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert not SegmentConfiguration.objects.filter(environment=environment).exists()
