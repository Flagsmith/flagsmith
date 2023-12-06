from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from rest_framework import status
from rest_framework.test import APIClient


def test_get_version_info(api_client: APIClient) -> None:
    # Given
    url = reverse("version-info")

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "ci_commit_sha": "unknown",
        "image_tag": "unknown",
        "is_enterprise": False,
    }


def test_get_index(api_client: APIClient, settings: SettingsWrapper) -> None:
    # Given
    url = reverse("index")
    settings.DISABLE_FLAGSMITH_UI = True

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
