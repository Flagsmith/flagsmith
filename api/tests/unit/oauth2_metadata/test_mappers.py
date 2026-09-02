from pytest_django.fixtures import SettingsWrapper

from oauth2_metadata.constants import SCOPE_ADMIN_API, SCOPE_GRANTS, SCOPE_MCP
from oauth2_metadata.mappers import map_scopes_to_descriptions


def test_map_scopes_to_descriptions__described_scopes__returns_labels_and_grants() -> (
    None
):
    # Given
    scopes = [SCOPE_MCP, SCOPE_ADMIN_API]

    # When
    descriptions = map_scopes_to_descriptions(scopes)

    # Then
    assert descriptions == {
        SCOPE_MCP: {
            "label": "MCP access",
            "grants": list(SCOPE_GRANTS[SCOPE_MCP]),
        },
        SCOPE_ADMIN_API: {
            "label": "Management API access",
            "grants": list(SCOPE_GRANTS[SCOPE_ADMIN_API]),
        },
    }


def test_map_scopes_to_descriptions__scope_without_grants__returns_label_only(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.OAUTH2_PROVIDER = {
        **settings.OAUTH2_PROVIDER,
        "SCOPES": {**settings.OAUTH2_PROVIDER["SCOPES"], "read": "Read access"},
    }

    # When
    descriptions = map_scopes_to_descriptions(["read"])

    # Then
    assert descriptions == {"read": {"label": "Read access", "grants": []}}


def test_map_scopes_to_descriptions__unregistered_scope__falls_back_to_its_name() -> (
    None
):
    # Given
    scopes = ["not-a-scope"]

    # When
    descriptions = map_scopes_to_descriptions(scopes)

    # Then
    assert descriptions == {"not-a-scope": {"label": "not-a-scope", "grants": []}}


def test_map_scopes_to_descriptions__no_scopes__returns_empty() -> None:
    # Given
    scopes: list[str] = []

    # When
    descriptions = map_scopes_to_descriptions(scopes)

    # Then
    assert descriptions == {}
