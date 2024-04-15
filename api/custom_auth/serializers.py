from django.conf import settings
from django.contrib.auth.signals import user_login_failed
from djoser.serializers import UserCreateSerializer, UserDeleteSerializer
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.validators import UniqueValidator
from trench.serializers import CodeLoginSerializer, LoginSerializer

from organisations.invites.models import Invite
from users.constants import DEFAULT_DELETE_ORPHAN_ORGANISATIONS_VALUE
from users.models import FFAdminUser, SignUpType

from .constants import USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE


class AuthControllerMixin(serializers.Serializer):
    def check_auth_method(self, email: str):
        """Helper to make pre-authentication checks and signal on failure"""

        if settings.AUTH_CONTROLLER_INSTALLED:
            from auth_controller.controller import (
                is_authentication_method_valid,
            )

            try:
                is_authentication_method_valid(
                    self.context.get("request"), email=email, raise_exception=True
                )
            except APIException as e:
                # catch and signal pre authenticate() login failure
                user_login_failed.send(
                    sender=self.__module__,
                    credentials={"username": email},
                    request=self.context["request"],
                    codes=e.get_codes(),
                )
                raise


class PostAuthenticateMixin(serializers.Serializer):
    """Extend serializer to signal on post-authentication failures"""

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except APIException as e:
            # catch and signal post authenticate() login failure
            # (assume django already sent a signal if self.user is not set)
            if user := getattr(self, "user", None):
                user_login_failed.send(
                    sender=self.__module__,
                    credentials={"username": user.natural_key()},
                    request=self.context["request"],
                    codes=e.get_codes(),
                )
            raise


class CustomLoginSerializer(
    AuthControllerMixin, PostAuthenticateMixin, LoginSerializer
):
    """Extend trench password login serializer to signal pre- and post-authentication failures"""

    def validate(self, attrs):
        # pre-authenticate() check/signal
        email = attrs.get("email")
        self.check_auth_method(email)
        # mixin will handle post-authenticate() check/signal
        return super().validate(attrs)


class CustomCodeLoginSerializer(PostAuthenticateMixin, CodeLoginSerializer):
    """Extend trench code login serializer to signal post-authentication failures"""


class CustomTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ("key",)


class CustomUserCreateSerializer(AuthControllerMixin, UserCreateSerializer):
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
                        message="Invalid email address.",
                    )
                ]
            }
        }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        email = attrs.get("email")
        self.check_auth_method(email)
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


class CustomUserDelete(UserDeleteSerializer):
    delete_orphan_organisations = serializers.BooleanField(
        default=DEFAULT_DELETE_ORPHAN_ORGANISATIONS_VALUE, required=False
    )
