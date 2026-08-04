import pytest
from pydantic import ValidationError

from flagsmith_mcp import config


def test_settings__unset__uses_saas_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given a clean environment
    for var in ("FLAGSMITH_API_URL", "FLAGSMITH_API_TOKEN", "TRANSPORT"):
        monkeypatch.delenv(var, raising=False)

    # When
    settings = config.Settings()

    # Then
    assert str(settings.flagsmith_api_url) == "https://api.flagsmith.com/"
    assert settings.flagsmith_api_token is None
    assert settings.transport == "http"


def test_settings__env__overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    monkeypatch.setenv("FLAGSMITH_API_URL", "https://self-hosted.example.com")
    monkeypatch.setenv("FLAGSMITH_API_TOKEN", "ser.secret")
    monkeypatch.setenv("TRANSPORT", "stdio")

    # When
    settings = config.Settings()

    # Then
    assert str(settings.flagsmith_api_url) == "https://self-hosted.example.com/"
    assert settings.flagsmith_api_token == "ser.secret"
    assert settings.transport == "stdio"


def test_settings__unsupported_transport__raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("TRANSPORT", "carrier-pigeon")

    # When / Then
    with pytest.raises(ValidationError):
        config.Settings()


def test_settings__stdio_without_token__raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given stdio transport but no API token
    monkeypatch.setenv("TRANSPORT", "stdio")
    monkeypatch.delenv("FLAGSMITH_API_TOKEN", raising=False)

    # When / Then
    with pytest.raises(ValidationError, match="FLAGSMITH_API_TOKEN is required"):
        config.Settings()
