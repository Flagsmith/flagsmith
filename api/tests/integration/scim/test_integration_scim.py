from typing import Any

import pytest
from django.conf import settings
from django.urls import resolve
from pytest_django.fixtures import SettingsWrapper
from rest_framework import status
from rest_framework.test import APIClient

pytestmark = pytest.mark.skipif(
    not settings.SCIM_INSTALLED,
    reason="scim module not installed (private package extra)",
)


def test_scim_settings__scim_installed__wires_apps_and_service_provider() -> None:
    # Given / When
    # Settings are imported at module load time.

    # Then
    assert settings.SCIM_INSTALLED is True
    assert "django_scim" in settings.INSTALLED_APPS
    assert "scim" in settings.INSTALLED_APPS
    service_provider: dict[str, Any] = settings.SCIM_SERVICE_PROVIDER
    assert service_provider["BULK"] == {"SUPPORTED": False}
    assert service_provider["CHANGE_PASSWORD"] == {"SUPPORTED": False}
    assert service_provider["ETAG"] == {"SUPPORTED": False}
    assert service_provider["FILTER"] == {"SUPPORTED": True, "MAX_RESULTS": 100}
    assert service_provider["SORT"] == {"SUPPORTED": False}
    assert service_provider["PATCH"] == {"SUPPORTED": True}
    assert (
        service_provider["AUTH_CHECK_MIDDLEWARE"]
        == "scim.middleware.ScimAuthenticationMiddleware"
    )
    assert service_provider["AUTHENTICATION_SCHEMES"][0]["type"] == "oauthbearertoken"


@pytest.mark.parametrize(
    "path, expected_url_name",
    [
        ("/api/v1/scim/v2/ServiceProviderConfig", "service-provider-config"),
        ("/api/v1/scim/v2/Schemas", "schemas"),
        ("/api/v1/scim/v2/ResourceTypes", "resource-types"),
        ("/api/v1/organisations/1/scim/", "scim-configuration"),
        (
            "/api/v1/organisations/1/scim/regenerate-token/",
            "scim-configuration-regenerate-token",
        ),
    ],
)
def test_scim_urls__scim_installed__resolve(path: str, expected_url_name: str) -> None:
    # Given / When
    match = resolve(path)

    # Then
    assert match.url_name == expected_url_name


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/scim/v2/ServiceProviderConfig",
        "/api/v1/scim/v2/Schemas",
        "/api/v1/scim/v2/ResourceTypes",
    ],
)
def test_scim_protocol_endpoint__no_bearer__returns_401(
    path: str,
) -> None:
    # Given
    client = APIClient()

    # When
    response = client.get(path)

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/scim/v2/ServiceProviderConfig",
        "/api/v1/scim/v2/Schemas",
        "/api/v1/scim/v2/ResourceTypes",
    ],
)
def test_scim_protocol_endpoint__valid_bearer_for_enterprise_org__returns_200(
    scim_client: "APIClient",
    scim_bearer_for_enterprise_org: str,
    path: str,
) -> None:
    # Given
    scim_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {scim_bearer_for_enterprise_org}"
    )

    # When
    response = scim_client.get(path)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_scim_protocol_endpoint__valid_bearer_for_non_enterprise_org__returns_403(
    scim_client: "APIClient",
    scim_bearer_for_non_enterprise_org: str,
) -> None:
    # Given
    scim_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {scim_bearer_for_non_enterprise_org}"
    )

    # When
    response = scim_client.get("/api/v1/scim/v2/ServiceProviderConfig")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_scim_service_provider_config__custom_host__uses_request_host_for_location(
    scim_client: "APIClient",
    scim_bearer_for_enterprise_org: str,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ALLOWED_HOSTS = ["scim.example.com", "testserver"]
    scim_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {scim_bearer_for_enterprise_org}"
    )

    # When
    response = scim_client.get(
        "/api/v1/scim/v2/ServiceProviderConfig",
        HTTP_HOST="scim.example.com",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        response.json()["meta"]["location"]
        == "http://scim.example.com/api/v1/scim/v2/ServiceProviderConfig"
    )
