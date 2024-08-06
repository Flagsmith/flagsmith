import pytest
from django.test import RequestFactory
from pytest_django.fixtures import SettingsWrapper
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import ModelSerializer

from custom_auth.constants import (
    USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE,
)
from custom_auth.serializers import (
    CustomUserCreateSerializer,
    InviteLinkValidationMixin,
)
from organisations.invites.models import InviteLink
from users.models import FFAdminUser, SignUpType

user_dict = {
    "email": "TestUser@mail.com",
    "password": "pass@word123",
    "first_name": "test",
    "last_name": "user",
}


def test_CustomUserCreateSerializer_converts_email_to_lower_case(
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


def test_CustomUserCreateSerializer_does_case_insensitive_lookup_with_email(
    db: None, rf: RequestFactory
) -> None:
    # Given
    request = rf.post("/api/v1/auth/users/")
    FFAdminUser.objects.create(email="testuser@mail.com")

    serializer = CustomUserCreateSerializer(
        data=user_dict, context={"request": request}
    )

    # When
    assert serializer.is_valid() is False
    assert serializer.errors["email"][0] == "Email already exists. Please log in."


def test_CustomUserCreateSerializer_calls_is_authentication_method_valid_correctly_if_auth_controller_is_installed(
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


def test_CustomUserCreateSerializer_allows_registration_if_sign_up_type_is_invite_link(
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


def test_invite_link_validation_mixin_validate_fails_if_invite_link_hash_not_provided(
    settings: SettingsWrapper,
    db: None,
) -> None:
    # Given
    settings.ALLOW_REGISTRATION_WITHOUT_INVITE = False

    class TestSerializer(InviteLinkValidationMixin, ModelSerializer):
        class Meta:
            model = FFAdminUser
            fields = ("sign_up_type",)

    serializer = TestSerializer(data={"sign_up_type": SignUpType.INVITE_LINK.value})

    # When
    with pytest.raises(PermissionDenied) as exc_info:
        serializer.is_valid(raise_exception=True)

    # Then
    assert exc_info.value.detail == USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE


def test_invite_link_validation_mixin_validate_fails_if_invite_link_hash_not_valid(
    invite_link: InviteLink,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ALLOW_REGISTRATION_WITHOUT_INVITE = False

    class TestSerializer(InviteLinkValidationMixin, ModelSerializer):
        class Meta:
            model = FFAdminUser
            fields = ("sign_up_type",)

    serializer = TestSerializer(
        data={
            "sign_up_type": SignUpType.INVITE_LINK.value,
            "invite_hash": "invalid-hash",
        }
    )

    # When
    with pytest.raises(PermissionDenied) as exc_info:
        serializer.is_valid(raise_exception=True)

    # Then
    assert exc_info.value.detail == USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE
