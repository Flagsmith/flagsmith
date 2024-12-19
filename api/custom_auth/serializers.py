from typing import Any

from django.conf import settings
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.validators import UniqueValidator

from organisations.invites.models import Invite, InviteLink
from users.auth_type import AuthType
from users.constants import DEFAULT_DELETE_ORPHAN_ORGANISATIONS_VALUE
from users.models import FFAdminUser, SignUpType

from .constants import (
    FIELD_BLANK_ERROR,
    INVALID_PASSWORD_ERROR,
    USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE,
)


class CustomTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ("key",)


class InviteLinkValidationMixin:
    invite_hash = serializers.CharField(required=False, write_only=True)

    def _validate_registration_invite(self, email: str, sign_up_type: str) -> None:
        if settings.ALLOW_REGISTRATION_WITHOUT_INVITE:
            return

        valid = False

        match sign_up_type:
            case SignUpType.INVITE_LINK.value:
                valid = InviteLink.objects.filter(
                    hash=self.initial_data.get("invite_hash")
                ).exists()
            case SignUpType.INVITE_EMAIL.value:
                valid = Invite.objects.filter(email__iexact=email.lower()).exists()

        if not valid:
            raise PermissionDenied(USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE)


class CustomUserCreateSerializer(UserCreateSerializer, InviteLinkValidationMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if not settings.COOKIE_AUTH_ENABLED:
            self.fields["key"] = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        fields = UserCreateSerializer.Meta.fields + (
            "is_active",
            "marketing_consent_given",
            "uuid",
        )
        read_only_fields = ("is_active", "uuid")
        write_only_fields = ("sign_up_type",)
        extra_kwargs = {
            "email": {
                "validators": [
                    UniqueValidator(
                        queryset=FFAdminUser.objects.all(),
                        lookup="iexact",
                        message="Email already exists. Please log in.",
                    )
                ]
            }
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        email = attrs.get("email")
        if settings.AUTH_CONTROLLER_INSTALLED:
            from auth_controller.controller import (
                is_authentication_method_valid,
            )

            is_authentication_method_valid(
                self.context.get("request"), email=email, raise_exception=True
            )

        self._validate_registration_invite(
            email=email, sign_up_type=attrs.get("sign_up_type")
        )

        attrs["email"] = email.lower()
        return attrs

    def save(self) -> FFAdminUser:
        instance = super().save()
        if "view" in self.context:
            self.context["view"].user = instance
        return instance

    @staticmethod
    def get_key(instance) -> str:
        token, _ = Token.objects.get_or_create(user=instance)
        return token.key


class CustomUserDelete(serializers.Serializer):
    current_password = serializers.CharField(
        style={"input_type": "password"},
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    default_error_messages = {
        "invalid_password": INVALID_PASSWORD_ERROR,
        "field_blank": FIELD_BLANK_ERROR,
    }

    def validate_current_password(self, value):
        user_auth_type = self.context["request"].user.auth_type
        if (
            user_auth_type == AuthType.GOOGLE.value
            or user_auth_type == AuthType.GITHUB.value
        ):
            return value

        if not value:
            return self.fail("field_blank")

        is_password_valid = self.context["request"].user.check_password(value)
        if is_password_valid:
            return value
        else:
            self.fail("invalid_password")

    delete_orphan_organisations = serializers.BooleanField(
        default=DEFAULT_DELETE_ORPHAN_ORGANISATIONS_VALUE, required=False
    )
