import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from integrations.new_relic.models import NewRelicConfiguration
from projects.models import Project


def test_new_relic_config__post_valid_data__creates_configuration(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    data = {
        "base_url": "http://test.com",
        "api_key": "key-123",
        "app_id": "app-123",
    }
    url = reverse("api-v1:projects:integrations-new-relic-list", args=[project.id])
    # When
    response = admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert NewRelicConfiguration.objects.filter(project=project).count() == 1


def test_new_relic_config__post_duplicate__returns_bad_request(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    NewRelicConfiguration.objects.create(
        base_url="http://test.com",
        api_key="key-123",
        app_id="app-123",
        project=project,
    )

    data = {
        "base_url": "http://test.com",
        "api_key": "key-123",
        "app_id": "app-123",
    }
    url = reverse("api-v1:projects:integrations-new-relic-list", args=[project.id])

    # When
    response = admin_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert NewRelicConfiguration.objects.filter(project=project).count() == 1


def test_new_relic_config__put_updated_data__updates_configuration(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    config = NewRelicConfiguration.objects.create(
        base_url="http://test.com",
        api_key="key-123",
        app_id="app-123",
        project=project,
    )

    api_key_updated = "new api"
    app_id_updated = "new app"
    data = {
        "base_url": config.base_url,
        "api_key": api_key_updated,
        "app_id": app_id_updated,
    }

    # When
    url = reverse(
        "api-v1:projects:integrations-new-relic-detail",
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
    assert config.app_id == app_id_updated


def test_new_relic_config__get_list__returns_configurations(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    config = NewRelicConfiguration.objects.create(
        base_url="http://test.com",
        api_key="key-123",
        app_id="app-123",
        project=project,
    )
    url = reverse("api-v1:projects:integrations-new-relic-list", args=[project.id])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data == [
        {
            "api_key": config.api_key,
            "app_id": config.app_id,
            "base_url": config.base_url,
            "id": config.id,
        }
    ]


def test_new_relic_config__delete_existing__removes_configuration(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    config = NewRelicConfiguration.objects.create(
        base_url="http://test.com",
        api_key="key-123",
        app_id="app-123",
        project=project,
    )
    # When
    url = reverse(
        "api-v1:projects:integrations-new-relic-detail",
        args=[project.id, config.id],
    )
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not NewRelicConfiguration.objects.filter(project=project).exists()


def test_new_relic_config__project_with_deleted_config__creates_new_configuration(  # type: ignore[no-untyped-def]
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
