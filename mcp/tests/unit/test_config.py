import pytest

from flagsmith_mcp import config


def test_get_api_url__unset__returns_saas_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.delenv("FLAGSMITH_API_URL", raising=False)

    # When
    api_url = config.get_api_url()

    # Then
    assert api_url == config.DEFAULT_API_URL


def test_get_api_url__set__returns_override(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    monkeypatch.setenv("FLAGSMITH_API_URL", "https://flagsmith.example.com")

    # When
    api_url = config.get_api_url()

    # Then
    assert api_url == "https://flagsmith.example.com"


def test_openapi_spec_url__api_url_overridden__stays_hardcoded_to_saas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("FLAGSMITH_API_URL", "https://self-hosted.example.com")

    # When
    api_url = config.get_api_url()

    # Then
    assert api_url == "https://self-hosted.example.com"
    assert config.OPENAPI_SPEC_URL == "https://api.flagsmith.com/api/v1/swagger.json"


def test_get_transport__unset__returns_http_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.delenv("TRANSPORT", raising=False)

    # When
    transport = config.get_transport()

    # Then
    assert transport == "http"


@pytest.mark.parametrize("value", ["http", "stdio"])
def test_get_transport__supported__returns_value(
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    # Given
    monkeypatch.setenv("TRANSPORT", value)

    # When
    transport = config.get_transport()

    # Then
    assert transport == value


def test_get_transport__unsupported__raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("TRANSPORT", "carrier-pigeon")

    # When / Then
    with pytest.raises(ValueError, match="carrier-pigeon"):
        config.get_transport()
