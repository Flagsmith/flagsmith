import typing

import pytest
from django.contrib.auth.models import AbstractUser
from django.test import RequestFactory
from djoser.serializers import TokenCreateSerializer  # type: ignore[import-untyped]
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework.exceptions import PermissionDenied

from custom_auth.constants import (
    USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE,
)
from custom_auth.serializers import CustomUserCreateSerializer
from organisations.invites.models import InviteLink
from users.models import FFAdminUser, SignUpType

user_dict = {
    "email": "TestUser@mail.com",
    "password": "pass@word123",
    "first_name": "test",
    "last_name": "user",
}


def test_custom_user_create_serializer__mixed_case_email__converts_to_lower_case(
    db: None, rf: RequestFactory
) -> None:
    # Given
    request = rf.post("/api/v1/auth/users/")
    serializer = CustomUserCreateSerializer(
        data=user_dict, context={"request": request}
    )
    # When
    serializer.is_valid(raise_exception=True)
    # Then
    assert serializer.validated_data["email"] == "testuser@mail.com"


def test_custom_user_create_serializer__duplicate_email_different_case__returns_error(
    db: None, rf: RequestFactory
) -> None:
    # Given
    request = rf.post("/api/v1/auth/users/")
    FFAdminUser.objects.create(email="testuser@mail.com")

    serializer = CustomUserCreateSerializer(
        data=user_dict, context={"request": request}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert serializer.errors["email"][0] == "Email already exists. Please log in."


def test_custom_user_create_serializer__auth_controller_installed__calls_is_authentication_method_valid(  # type: ignore[no-untyped-def]  # noqa: E501
    db, settings, mocker, rf
):
    # Given
    settings.AUTH_CONTROLLER_INSTALLED = True

    request = rf.post("/v1/auth/login")
    mocked_auth_controller = mocker.MagicMock()
    mocker.patch.dict(
        "sys.modules", {"auth_controller.controller": mocked_auth_controller}
    )

    # When
    serializer = CustomUserCreateSerializer(
        data=user_dict, context={"request": request}
    )

    serializer.is_valid(raise_exception=True)

    # Then
    mocked_auth_controller.is_authentication_method_valid.assert_called_with(
        request,
        email=user_dict["email"],
        raise_exception=True,
    )


def test_custom_user_create_serializer__sign_up_type_invite_link__allows_registration(
    invite_link: InviteLink,
    db: None,
    settings: SettingsWrapper,
    rf: RequestFactory,
) -> None:
    # Given
    settings.ALLOW_REGISTRATION_WITHOUT_INVITE = False

    data = {
        **user_dict,
        "sign_up_type": SignUpType.INVITE_LINK.value,
        "invite_hash": invite_link.hash,
    }

    serializer = CustomUserCreateSerializer(
        data=data, context={"request": rf.post("/api/v1/auth/users/")}
    )
    assert serializer.is_valid()

    # When
    user = serializer.save()

    # Then
    assert user


def test_invite_link_validation__hash_not_provided__raises_permission_denied(
    settings: SettingsWrapper,
    db: None,
) -> None:
    # Given
    settings.ALLOW_REGISTRATION_WITHOUT_INVITE = False

    serializer = CustomUserCreateSerializer(
        data={
            **user_dict,
            "sign_up_type": SignUpType.INVITE_LINK.value,
        }
    )

    # When
    with pytest.raises(PermissionDenied) as exc_info:
        serializer.is_valid(raise_exception=True)

    # Then
    assert exc_info.value.detail == USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE


def test_invite_link_validation__invalid_hash__raises_permission_denied(
    invite_link: InviteLink,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ALLOW_REGISTRATION_WITHOUT_INVITE = False

    serializer = CustomUserCreateSerializer(
        data={
            **user_dict,
            "sign_up_type": SignUpType.INVITE_LINK.value,
            "invite_hash": "invalid-hash",
        }
    )

    # When
    with pytest.raises(PermissionDenied) as exc_info:
        serializer.is_valid(raise_exception=True)

    # Then
    assert exc_info.value.detail == USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE


@pytest.fixture
def django_ldap_username_field(
    django_user_model: type[AbstractUser],
) -> typing.Generator[str, None, None]:
    ldap_username_field = "username"
    username_field = django_user_model.USERNAME_FIELD
    django_user_model.USERNAME_FIELD = ldap_username_field
    yield ldap_username_field
    django_user_model.USERNAME_FIELD = username_field


# Previously, Djoser's default `TokenCreateSerializer` only respected the
# Djoser `LOGIN_FIELD` setting so it was impossible to grab the email from
# serializer and send it as a username to the login backend — which is required for LDAP to work.
# After Djoser 2.3.0, it's possible to alter `TokenCreateSerializer` behaviour
# to support this by setting the Django user model's `USERNAME_FIELD` constant
# to `"username"`, and Djoser's `LOGIN_FIELD` to `"email"`.
# This test is here to make sure Djoser behaves as expected.
def test_djoser_token_create_serializer__user_model_username_field__call_expected(
    mocker: MockerFixture,
    django_ldap_username_field: str,
) -> None:
    # Given
    expected_username = "some_username"
    expected_password = "some_password"

    mocked_authenticate = mocker.patch("djoser.serializers.authenticate")
    serializer = TokenCreateSerializer(
        data={"email": expected_username, "password": expected_password}
    )
    expected_authenticate_kwargs = {
        "request": None,
        django_ldap_username_field: expected_username,
        "password": expected_password,
    }

    # When
    serializer.is_valid(raise_exception=True)

    # Then
    mocked_authenticate.assert_called_with(**expected_authenticate_kwargs)
