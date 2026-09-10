from unittest import mock

from pytest_django.fixtures import SettingsWrapper

from custom_auth.permissions import IsSignupAllowed
from organisations.invites.models import Invite, InviteLink
from organisations.models import Organisation
from users.models import SignUpType


def test_is_signup_allowed__prevent_signup_disabled__returns_true(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.PREVENT_SIGNUP = False
    permission = IsSignupAllowed()
    mock_request = mock.MagicMock(data={})

    # When
    result = permission.has_permission(mock_request, mock.MagicMock())

    # Then
    assert result is True


def test_is_signup_allowed__prevent_signup_enabled_no_invite__returns_false(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.PREVENT_SIGNUP = True
    permission = IsSignupAllowed()
    mock_request = mock.MagicMock(data={"email": "test@example.com"})

    # When
    result = permission.has_permission(mock_request, mock.MagicMock())

    # Then
    assert result is False


def test_is_signup_allowed__prevent_signup_enabled_valid_invite_link__returns_true(
    db: None,
    settings: SettingsWrapper,
    organisation: Organisation,
) -> None:
    # Given
    settings.PREVENT_SIGNUP = True
    invite_link = InviteLink.objects.create(organisation=organisation)
    permission = IsSignupAllowed()
    mock_request = mock.MagicMock(
        data={
            "email": "test@example.com",
            "sign_up_type": SignUpType.INVITE_LINK.value,
            "invite_hash": invite_link.hash,
        }
    )

    # When
    result = permission.has_permission(mock_request, mock.MagicMock())

    # Then
    assert result is True


def test_is_signup_allowed__prevent_signup_enabled_invalid_invite_hash__returns_false(
    db: None,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.PREVENT_SIGNUP = True
    permission = IsSignupAllowed()
    mock_request = mock.MagicMock(
        data={
            "email": "test@example.com",
            "sign_up_type": SignUpType.INVITE_LINK.value,
            "invite_hash": "invalid-hash",
        }
    )

    # When
    result = permission.has_permission(mock_request, mock.MagicMock())

    # Then
    assert result is False


def test_is_signup_allowed__prevent_signup_enabled_valid_invite_email__returns_true(
    db: None,
    settings: SettingsWrapper,
    organisation: Organisation,
) -> None:
    # Given
    settings.PREVENT_SIGNUP = True
    Invite.objects.create(email="test@example.com", organisation=organisation)
    permission = IsSignupAllowed()
    mock_request = mock.MagicMock(
        data={
            "email": "Test@Example.com",
            "sign_up_type": SignUpType.INVITE_EMAIL.value,
        }
    )

    # When
    result = permission.has_permission(mock_request, mock.MagicMock())

    # Then
    assert result is True
