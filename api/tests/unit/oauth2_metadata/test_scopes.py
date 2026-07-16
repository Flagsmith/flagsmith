from oauth2_provider.models import Application
from oauth2_provider.scopes import get_scopes_backend

from oauth2_metadata.constants import (
    FLAGSMITH_CLI_CLIENT_ID,
    SCOPE_ADMIN_API,
    SCOPE_MCP,
)
from oauth2_metadata.scopes import FlagsmithScopes
from oauth2_metadata.services import create_oauth2_application


def test_get_scopes_backend__default_settings__returns_flagsmith_scopes() -> None:
    # Given / When
    backend = get_scopes_backend()

    # Then
    assert isinstance(backend, FlagsmithScopes)


def test_get_available_scopes__flagsmith_cli_application__admin_api_only(
    db: None,
) -> None:
    # Given
    application = Application.objects.get(client_id=FLAGSMITH_CLI_CLIENT_ID)

    # When
    scopes = FlagsmithScopes().get_available_scopes(application=application)

    # Then
    assert set(scopes) == {SCOPE_ADMIN_API}


def test_get_available_scopes__dcr_registered_application__excludes_admin_api(
    db: None,
) -> None:
    # Given
    application = create_oauth2_application(
        client_name="Third Party App",
        redirect_uris=["https://example.com/callback"],
    )

    # When
    scopes = FlagsmithScopes().get_available_scopes(application=application)

    # Then
    assert set(scopes) == {SCOPE_MCP}


def test_get_available_scopes__no_application__excludes_admin_api() -> None:
    # Given / When
    scopes = FlagsmithScopes().get_available_scopes()

    # Then
    assert set(scopes) == {SCOPE_MCP}


def test_get_default_scopes__flagsmith_cli_application__no_defaults(
    db: None,
) -> None:
    # Given
    application = Application.objects.get(client_id=FLAGSMITH_CLI_CLIENT_ID)

    # When
    scopes = FlagsmithScopes().get_default_scopes(application=application)

    # Then
    assert scopes == []


def test_get_default_scopes__dcr_registered_application__defaults_to_mcp(
    db: None,
) -> None:
    # Given
    application = create_oauth2_application(
        client_name="Third Party App",
        redirect_uris=["https://example.com/callback"],
    )

    # When
    scopes = FlagsmithScopes().get_default_scopes(application=application)

    # Then
    assert scopes == [SCOPE_MCP]
