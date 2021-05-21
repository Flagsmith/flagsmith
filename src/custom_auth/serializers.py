from django.conf import settings
from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import PermissionDenied

from organisations.invites.models import Invite

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
        fields = UserCreateSerializer.Meta.fields + ("is_active",)
        read_only_fields = ("is_active",)

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
