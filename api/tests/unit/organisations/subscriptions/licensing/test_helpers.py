import json

import pytest
from pytest_django.fixtures import SettingsWrapper

from organisations.subscriptions.licensing.helpers import (
    PrivateKeyMissingError,
    create_private_key,
    create_public_key,
    sign_licence,
    verify_signature,
)


def test_sign_and_verify_signature_of_licence() -> None:
    # Given
    licence_content = {
        "organisation_name": "Test Organisation",
        "plan_id": "Enterprise",
        "num_seats": 20,
        "num_projects": 3,
        "num_api_calls": 3_000_000,
    }

    licence = json.dumps(licence_content)

    # When
    licence_signature = sign_licence(licence)
    signature_verification = verify_signature(licence, licence_signature)

    # Then
    assert licence_signature
    assert signature_verification is True


def test_sign_and_verify_signature_of_licence_when_signature_fails(
    settings: SettingsWrapper,
) -> None:
    # Given
    # Change the public key information so the signature fails
    settings.SUBSCRIPTION_LICENCE_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtKOkPiegKyWdsUcmUOXv
bnunQeG4B+yOw2GG/bfXiG+ec9L2WVlSy5iK/p4AnwsSHj6gnJawHp/YK6wkYcgF
w/l2WI0T9MNsJagN+uxyV27YtWnV50JzOEFyEzSYUZxqKokVce70PypbqfsjASTl
OCJJErEGgIKdHk3T5RpQPigHwh9/a7KiBzV7ktan7KSNkcmketd9Db0eg+KdO1yZ
bNQGDrPMaYXVpfG+Ic2yU7wtCKkYb1/s+JBMkI6a3XH8DhuKq6rSG+GrJttYpjrR
PAhkbx1Jf3FftZf4YL9X3W3ghczPPatemfylyAFiTGH5FrjlhlRJn+8owfWjK3zN
3wIDAQAC
-----END PUBLIC KEY-----
    """

    licence_content = {
        "organisation_name": "Test Organisation",
        "plan_id": "Enterprise",
        "num_seats": 20,
        "num_projects": 3,
        "num_api_calls": 3_000_000,
    }

    licence = json.dumps(licence_content)

    # When
    licence_signature = sign_licence(licence)
    signature_verification = verify_signature(licence, licence_signature)

    # Then
    assert signature_verification is False


def test_sign_licence_with_missing_private_key(settings: SettingsWrapper) -> None:
    # Given
    settings.SUBSCRIPTION_LICENCE_PRIVATE_KEY = None
    licence_content = {
        "organisation_name": "Test Organisation",
        "plan_id": "Enterprise",
        "num_seats": 20,
        "num_projects": 3,
        "num_api_calls": 3_000_000,
    }

    licence = json.dumps(licence_content)

    # When
    with pytest.raises(PrivateKeyMissingError) as exception:
        sign_licence(licence)

    # Then
    assert str(exception.value) == "Private key is missing"


def test_create_public_key() -> None:
    # Given / When
    public_key = create_public_key()

    # Then
    assert "BEGIN PUBLIC KEY" in public_key


def test_create_private_key() -> None:
    # Given / When
    private_key = create_private_key()

    # Then
    assert "BEGIN PRIVATE KEY" in private_key
