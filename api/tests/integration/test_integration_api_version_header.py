import pytest
from common.core.utils import get_file_contents, get_versions_from_manifest
from pyfakefs.fake_filesystem import FakeFilesystem
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def clear_lru_caches() -> None:
    get_file_contents.cache_clear()
    get_versions_from_manifest.cache_clear()


@pytest.mark.parametrize(
    "url",
    [
        "/robots.txt",
        "/api/v1/auth/users/me/",
    ],
)
@pytest.mark.parametrize(
    "version_file_contents, expected_version",
    [
        ('{".": "v1.2.3"}', "v1.2.3"),
        ('{"foo": "bar"}', "unknown"),
        ("", "unknown"),
    ],
)
def test_api_version_header__success_response__returns_expected_version(
    admin_client: APIClient,
    expected_version: str,
    fs: FakeFilesystem,
    url: str,
    version_file_contents: str,
) -> None:
    # Given
    fs.create_file(".versions.json", contents=version_file_contents)

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Flagsmith-Version"] == expected_version


@pytest.mark.parametrize(
    "version_file_contents, expected_version",
    [
        ('{".": "v1.2.3"}', "v1.2.3"),
        ('{"foo": "bar"}', "unknown"),
        ("", "unknown"),
    ],
)
def test_api_version_header__error_response__returns_expected_version(
    client: APIClient,
    expected_version: str,
    fs: FakeFilesystem,
    version_file_contents: str,
) -> None:
    # Given
    fs.create_file(".versions.json", contents=version_file_contents)

    # When
    response = client.get("/wat")

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["Flagsmith-Version"] == expected_version
