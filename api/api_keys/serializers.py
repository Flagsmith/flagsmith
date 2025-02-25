from django.conf import settings
from rest_framework import serializers

from .models import MasterAPIKey


class MasterAPIKeySerializer(serializers.ModelSerializer):  # type: ignore[type-arg]
    key = serializers.CharField(
        read_only=True,
        help_text="Since we don't store the api key itself(i.e: we only store the hash) this key will be none "
        "for every endpoint apart from create",
    )
    is_admin = serializers.BooleanField(default=True)

    class Meta:
        model = MasterAPIKey
        fields = (
            "id",
            "prefix",
            "created",
            "name",
            "revoked",
            "expiry_date",
            "key",
            "is_admin",
            "has_expired",
        )
        read_only_fields = ("prefix", "created", "key")

    def create(self, validated_data):  # type: ignore[no-untyped-def]
        obj, key = MasterAPIKey.objects.create_key(**validated_data)
        obj.key = key  # type: ignore[attr-defined]
        return obj

    def validate_is_admin(self, is_admin: bool):  # type: ignore[no-untyped-def]
        if is_admin is False and not settings.IS_RBAC_INSTALLED:
            raise serializers.ValidationError(
                "RBAC is not installed, cannot create non-admin key"
            )
        return is_admin
