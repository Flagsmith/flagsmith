from django.conf import settings
from django.test import Client


def test_api_documentation_specification_loads(
    client: Client,
) -> None:
    # When
    # Request JSON format via Accept header (drf-spectacular defaults to YAML).
    response = client.get("/api/v1/swagger.json", HTTP_ACCEPT="application/json")

    # Then
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Flagsmith API"


def test_spectacular_settings__component_split_request__is_enabled() -> None:
    assert settings.SPECTACULAR_SETTINGS["COMPONENT_SPLIT_REQUEST"] is True
