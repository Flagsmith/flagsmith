import pytest
from cryptography.fernet import InvalidToken
from pytest_django.fixtures import SettingsWrapper

from core.warehouse_credentials import (
    decrypt_warehouse_credentials,
    encrypt_warehouse_credentials,
)


def test_encrypt_warehouse_credentials__value__comes_back_intact_under_the_same_secret() -> (
    None
):
    # Given / When
    token = encrypt_warehouse_credentials({"password": "hunter2"})

    # Then the value is unreadable as stored and decrypts to what went in
    assert "hunter2" not in token
    assert decrypt_warehouse_credentials(token) == {"password": "hunter2"}


def test_decrypt_warehouse_credentials__token_from_another_secret__raises_invalid_token(
    settings: SettingsWrapper,
) -> None:
    # Given a token made under one secret
    settings.WAREHOUSE_CREDENTIALS_SECRET = "old-secret"
    token = encrypt_warehouse_credentials({"password": "hunter2"})

    # When the secret has changed
    settings.WAREHOUSE_CREDENTIALS_SECRET = "new-secret"

    # Then the caller learns the token is unreadable rather than getting garbage
    with pytest.raises(InvalidToken):
        decrypt_warehouse_credentials(token)
