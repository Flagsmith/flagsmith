import pytest
from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured
from pytest_django.fixtures import SettingsWrapper
from pytest_structlog import StructuredLogCapture

from core.fields import EncryptedJSONField


@pytest.fixture()
def encryption_keys(settings: SettingsWrapper) -> list[str]:
    keys = [Fernet.generate_key().decode()]
    settings.CREDENTIALS_ENCRYPTION_KEYS = keys
    return keys


def test_get_prep_value__json_value__returns_ciphertext_that_roundtrips(
    encryption_keys: list[str],
) -> None:
    # Given
    field = EncryptedJSONField()
    value = {"password": "hunter2"}

    # When
    stored = field.get_prep_value(value)

    # Then
    assert stored is not None
    assert "hunter2" not in stored
    assert field.from_db_value(stored, None, None) == value


def test_get_prep_value__none__returns_none(
    encryption_keys: list[str],
) -> None:
    # Given
    field = EncryptedJSONField()

    # When & Then
    assert field.get_prep_value(None) is None


def test_from_db_value__none__returns_none(
    encryption_keys: list[str],
) -> None:
    # Given
    field = EncryptedJSONField()

    # When & Then
    assert field.from_db_value(None, None, None) is None


def test_get_prep_value__no_keys_configured__raises_improperly_configured(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.CREDENTIALS_ENCRYPTION_KEYS = []
    field = EncryptedJSONField()

    # When & Then
    with pytest.raises(ImproperlyConfigured):
        field.get_prep_value({"password": "hunter2"})


def test_from_db_value__new_key_prepended__old_token_still_decrypts(
    settings: SettingsWrapper,
) -> None:
    # Given
    old_key = Fernet.generate_key().decode()
    settings.CREDENTIALS_ENCRYPTION_KEYS = [old_key]
    field = EncryptedJSONField()
    stored = field.get_prep_value({"password": "hunter2"})

    # When
    settings.CREDENTIALS_ENCRYPTION_KEYS = [Fernet.generate_key().decode(), old_key]

    # Then
    assert field.from_db_value(stored, None, None) == {"password": "hunter2"}


def test_from_db_value__token_key_removed_from_ring__returns_none_and_logs(
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.CREDENTIALS_ENCRYPTION_KEYS = [Fernet.generate_key().decode()]
    field = EncryptedJSONField()
    stored = field.get_prep_value({"password": "hunter2"})
    settings.CREDENTIALS_ENCRYPTION_KEYS = [Fernet.generate_key().decode()]

    # When
    value = field.from_db_value(stored, None, None)

    # Then
    assert value is None
    assert {
        "level": "warning",
        "event": "encrypted_field.decrypt_failed",
    } in [{"level": e["level"], "event": e["event"]} for e in log.events]


def test_from_db_value__malformed_key_in_ring__returns_none_and_logs(
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.CREDENTIALS_ENCRYPTION_KEYS = [Fernet.generate_key().decode()]
    field = EncryptedJSONField()
    stored = field.get_prep_value({"password": "hunter2"})
    settings.CREDENTIALS_ENCRYPTION_KEYS = [Fernet.generate_key().decode(), ""]

    # When
    value = field.from_db_value(stored, None, None)

    # Then
    assert value is None
    assert any(e["event"] == "encrypted_field.decrypt_failed" for e in log.events)


def test_from_db_value__no_keys_configured__returns_none_and_logs(
    settings: SettingsWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.CREDENTIALS_ENCRYPTION_KEYS = [Fernet.generate_key().decode()]
    field = EncryptedJSONField()
    stored = field.get_prep_value({"password": "hunter2"})
    settings.CREDENTIALS_ENCRYPTION_KEYS = []

    # When
    value = field.from_db_value(stored, None, None)

    # Then
    assert value is None
    assert any(e["event"] == "encrypted_field.decrypt_failed" for e in log.events)


def test_get_lookup__non_isnull__raises_not_implemented(
    encryption_keys: list[str],
) -> None:
    # Given
    field = EncryptedJSONField()

    # When & Then
    with pytest.raises(NotImplementedError):
        field.get_lookup("exact")
    assert field.get_lookup("isnull") is not None
