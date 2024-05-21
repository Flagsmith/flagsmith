from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from app.utils import UNKNOWN


def test_get_version_info(api_client: APIClient, mocker: MockerFixture) -> None:
    # Given
    url = reverse("version-info")

    mocker.patch("app.utils.is_saas", return_value=False)
    mocker.patch("app.utils.is_enterprise", return_value=False)
    mocker.patch("app.utils._get_file_contents", return_value=UNKNOWN)

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "ci_commit_sha": UNKNOWN,
        "image_tag": UNKNOWN,
        "is_enterprise": False,
        "is_saas": False,
    }
