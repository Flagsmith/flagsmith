import json

import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_user_throttle_can_throttle_admin_endpoints(
    client: APIClient, project: int, mocker: MockerFixture, reset_cache: None
) -> None:
    # Given
    mocker.patch("core.throttling.UserRateThrottle.get_rate", return_value="1/minute")

    url = reverse("api-v1:projects:project-list")

    # Then - first request should be successful
    response = client.get(url, content_type="application/json")
    assert response.status_code == status.HTTP_200_OK

    # Second request should be throttled
    response = client.get(url, content_type="application/json")
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_get_flags_is_not_throttled_by_user_throttle(
    sdk_client: APIClient,
    environment: int,
    environment_api_key: str,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("core.throttling.UserRateThrottle.get_rate", return_value="1/minute")

    url = reverse("api-v1:flags")

    # When
    for _ in range(10):
        response = sdk_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK


def test_get_environment_document_is_not_throttled_by_user_throttle(
    server_side_sdk_client: APIClient,
    environment: int,
    environment_api_key: str,
    mocker: MockerFixture,
):
    # Given
    mocker.patch("core.throttling.UserRateThrottle.get_rate", return_value="1/minute")

    url = reverse("api-v1:environment-document")

    # When
    for _ in range(10):
        response = server_side_sdk_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK


def test_get_identities_is_not_throttled_by_user_throttle(
    environment: int,
    sdk_client: APIClient,
    mocker: MockerFixture,
    identity: int,
    identity_identifier: str,
):
    # Given
    mocker.patch("core.throttling.UserRateThrottle.get_rate", return_value="1/minute")

    base_url = reverse("api-v1:sdk-identities")
    url = f"{base_url}?identifier={identity_identifier}"

    # When
    for _ in range(10):
        response = sdk_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK


def test_set_trait_for_an_identity_is_not_throttled_by_user_throttle(
    environment: int,
    server_side_sdk_client: APIClient,
    identity: int,
    identity_identifier: str,
    mocker: MockerFixture,
):
    # Given
    mocker.patch("core.throttling.UserRateThrottle.get_rate", return_value="1/minute")
    url = reverse("api-v1:sdk-traits-list")
    data = {
        "identity": {"identifier": identity_identifier},
        "trait_key": "key",
        "trait_value": "value",
    }

    # When
    for _ in range(10):
        res = server_side_sdk_client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert res.status_code == status.HTTP_200_OK


def test_sdk_analytics_is_not_throttled_by_user_throttle(
    mocker: MockerFixture, environment: int, sdk_client: APIClient
):
    # Given
    mocker.patch("core.throttling.UserRateThrottle.get_rate", return_value="1/minute")

    # When
    for _ in range(10):
        response = sdk_client.post("/api/v1/analytics/flags/")

        # Then
        assert response.status_code == status.HTTP_200_OK


def test_self_hosted_telemetry_view_is_not_throttled_by_user_throttle(
    mocker: MockerFixture,
):
    # Given
    api_client = APIClient()
    mocker.patch("core.throttling.UserRateThrottle.get_rate", return_value="1/minute")

    data = {
        "organisations": 1,
        "projects": 1,
        "environments": 1,
        "features": 1,
        "segments": 1,
        "users": 1,
        "debug_enabled": True,
        "env": "test",
    }
    # When
    for _ in range(10):
        response = api_client.post("/api/v1/analytics/telemetry/", data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
