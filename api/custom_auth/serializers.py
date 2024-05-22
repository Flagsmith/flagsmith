from django.conf import settings
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied
from rest_framework.validators import UniqueValidator

from organisations.invites.models import Invite
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


class CustomUserCreateSerializer(UserCreateSerializer):
    key = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        fields = UserCreateSerializer.Meta.fields + (
            "is_active",
            "marketing_consent_given",
            "key",
        )
        read_only_fields = ("is_active",)
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

        attrs["email"] = email.lower()
        return attrs

    @staticmethod
    def get_key(instance):
        token, _ = Token.objects.get_or_create(user=instance)
        return token.key

    def save(self, **kwargs):
        if not (
            settings.ALLOW_REGISTRATION_WITHOUT_INVITE
            or self.validated_data.get("sign_up_type") == SignUpType.INVITE_LINK.value
            or Invite.objects.filter(email=self.validated_data.get("email"))
        ):
            raise PermissionDenied(USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE)

        return super(CustomUserCreateSerializer, self).save(**kwargs)


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
