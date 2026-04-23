from pytest_django.fixtures import SettingsWrapper

from edge_api.utils import is_edge_enabled


def test_is_edge_enabled__setting_true__returns_true(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.EDGE_ENABLED = True

    # When
    result = is_edge_enabled()

    # Then
    assert result is True


def test_is_edge_enabled__setting_false__returns_false(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.EDGE_ENABLED = False

    # When
    result = is_edge_enabled()

    # Then
    assert result is False
