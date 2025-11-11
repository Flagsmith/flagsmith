from datetime import datetime

from api_keys.models import MasterAPIKey
from users.models import FFAdminUser
from webhooks import mappers as webhook_mappers


def test_datetime_to_webhook_timestamp() -> None:
    # Given
    dt = datetime(2024, 1, 15, 14, 30, 45, 123456)

    # When
    result = webhook_mappers.datetime_to_webhook_timestamp(dt)

    # Then
    assert result == "2024-01-15T14:30:45.123456Z"


def test_user_or_key_to_changed_by_with_user(
    staff_user: FFAdminUser,
) -> None:
    # When
    result = webhook_mappers.user_or_key_to_changed_by(user=staff_user, api_key=None)

    # Then
    assert result == staff_user.email


def test_user_or_key_to_changed_by_with_api_key(
    master_api_key_object: MasterAPIKey,
) -> None:
    # When
    result = webhook_mappers.user_or_key_to_changed_by(
        user=None, api_key=master_api_key_object
    )

    # Then
    assert result == master_api_key_object.name


def test_user_or_key_to_changed_by_with_both_user_and_api_key_prefers_user(
    staff_user: FFAdminUser,
    master_api_key_object: MasterAPIKey,
) -> None:
    # When
    result = webhook_mappers.user_or_key_to_changed_by(
        user=staff_user, api_key=master_api_key_object
    )

    # Then
    assert result == staff_user.email


def test_user_or_key_to_changed_by_with_neither_returns_empty_string() -> None:
    # When
    result = webhook_mappers.user_or_key_to_changed_by(user=None, api_key=None)

    # Then
    assert result == ""
