from django.conf import settings
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied

from organisations.invites.models import Invite
from users.models import FFAdminUser

from .constants import USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE


class CustomTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ("key",)


class CustomUserCreateSerializer(UserCreateSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["key"] = serializers.SerializerMethodField()

    class Meta(UserCreateSerializer.Meta):
        fields = UserCreateSerializer.Meta.fields + ("is_active", "is_subscribed")
        read_only_fields = ("is_active",)

    def validate_email(self, value):
        if FFAdminUser.objects.filter(email__iexact=value).count() != 0:
            raise serializers.ValidationError(
                "Feature flag admin user with this email already exists."
            )

        return value.lower()

    @staticmethod
    def get_key(instance):
        token, _ = Token.objects.get_or_create(user=instance)
        return token.key

    def save(self, **kwargs):
        if not (
            settings.ALLOW_REGISTRATION_WITHOUT_INVITE
            or Invite.objects.filter(email=self.validated_data.get("email"))
        ):
            raise PermissionDenied(USER_REGISTRATION_WITHOUT_INVITE_ERROR_MESSAGE)

        return super(CustomUserCreateSerializer, self).save(**kwargs)
