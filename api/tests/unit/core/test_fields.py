import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_structlog import StructuredLogCapture

from core.fields import EncryptedJSONField


def test_get_prep_value__json_value__returns_ciphertext_that_roundtrips() -> None:
    # Given
    field = EncryptedJSONField()
    value = {"password": "hunter2"}

    # When
    stored = field.get_prep_value(value)

    # Then
    assert stored is not None
    assert "hunter2" not in stored
    assert field.from_db_value(stored, None, None) == value


def test_field_methods__none__returns_none() -> None:
    # Given
    field = EncryptedJSONField()

    # When & Then
    assert field.get_prep_value(None) is None
    assert field.from_db_value(None, None, None) is None


def test_from_db_value__secret_key_changed__returns_none_and_logs(
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.WAREHOUSE_CREDENTIALS_SECRET = "old-secret"
    field = EncryptedJSONField()
    stored = field.get_prep_value({"password": "hunter2"})
    settings.WAREHOUSE_CREDENTIALS_SECRET = "new-secret"

    # When
    value = field.from_db_value(stored, None, None)

    # Then
    assert value is None
    assert {
        "level": "warning",
        "event": "encrypted_field.decrypt_failed",
    } in [{"level": e["level"], "event": e["event"]} for e in log.events]


def test_get_lookup__non_isnull__raises_not_implemented() -> None:
    # Given
    field = EncryptedJSONField()

    # When & Then
    with pytest.raises(NotImplementedError):
        field.get_lookup("exact")
    assert field.get_lookup("isnull") is not None
