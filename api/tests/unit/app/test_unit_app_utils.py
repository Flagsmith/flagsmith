import pytest

from app.utils import get_numbered_env_vars_with_prefix


def test_get_numbered_env_vars_with_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    # Given
    monkeypatch.setenv("DB_URL_0", "0")
    monkeypatch.setenv("DB_URL_1", "1")
    monkeypatch.setenv("DB_URL_3", "3")

    # When
    env_vars = get_numbered_env_vars_with_prefix("DB_URL_")

    # Then
    assert env_vars == ["0", "1"]
