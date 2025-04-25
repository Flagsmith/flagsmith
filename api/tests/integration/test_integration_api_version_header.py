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
        # TODO: Add other GET-only URLs
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
def test_api_version_is_added_to_success_response_headers(
    client: APIClient,
    expected_version: str,
    fs: FakeFilesystem,
    url: str,
    version_file_contents: str,
) -> None:
    fs.create_file(".versions.json", contents=version_file_contents)

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Flagsmith-Version"] == expected_version


@pytest.mark.parametrize(
    "url",
    [
        "/wat",
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
def test_api_version_is_added_to_error_response_headers(
    client: APIClient,
    expected_version: str,
    fs: FakeFilesystem,
    url: str,
    version_file_contents: str,
) -> None:
    fs.create_file(".versions.json", contents=version_file_contents)

    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.headers["Flagsmith-Version"] == expected_version
