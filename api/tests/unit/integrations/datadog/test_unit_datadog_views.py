import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from integrations.datadog.models import DataDogConfiguration
from projects.models import Project


def test_should_create_datadog_config_when_post(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    data = {
        "base_url": "http://test.com",
        "api_key": "abc-123",
        "use_custom_source": True,
    }
    url = reverse("api-v1:projects:integrations-datadog-list", args=[project.id])
    # When
    response = admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert DataDogConfiguration.objects.filter(project=project).count() == 1

    created_config = DataDogConfiguration.objects.filter(project=project).first()
    assert created_config.base_url == data["base_url"]
    assert created_config.api_key == data["api_key"]
    assert created_config.use_custom_source == data["use_custom_source"]


def test_should_return_400_when_duplicate_datadog_config_is_posted(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    DataDogConfiguration.objects.create(
        base_url="http://test.com", api_key="api_123", project=project
    )
    data = {"base_url": "http://test.com", "api_key": "abc-123"}
    url = reverse("api-v1:projects:integrations-datadog-list", args=[project.id])

    # When
    response = admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert DataDogConfiguration.objects.filter(project=project).count() == 1


def test_should_update_configuration_when_put(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    config = DataDogConfiguration.objects.create(
        base_url="http://test.com", api_key="api_123", project=project
    )
    api_key_updated = "new api"
    data = {"base_url": config.base_url, "api_key": api_key_updated}

    # When
    url = reverse(
        "api-v1:projects:integrations-datadog-detail",
        args=[project.id, config.id],
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


def test_should_return_datadog_config_list_when_requested(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    config = DataDogConfiguration.objects.create(
        base_url="http://test.com", api_key="api_123", project=project
    )
    url = reverse("api-v1:projects:integrations-datadog-list", args=[project.id])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data == [
        {
            "api_key": config.api_key,
            "base_url": config.base_url,
            "id": config.id,
            "use_custom_source": False,
        }
    ]


def test_should_remove_configuration_when_delete(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    config = DataDogConfiguration.objects.create(
        base_url="http://test.com", api_key="api_123", project=project
    )
    # When
    url = reverse(
        "api-v1:projects:integrations-datadog-detail",
        args=[project.id, config.id],
    )
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not DataDogConfiguration.objects.filter(project=project).exists()


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
