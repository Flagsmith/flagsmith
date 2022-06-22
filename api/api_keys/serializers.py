from rest_framework import serializers

from .models import MasterAPIKey


class MasterAPIKeySerializer(serializers.ModelSerializer):
    key = serializers.CharField(
        read_only=True,
        help_text="Since we don't store the api key itself(i.e: we only store the hash) this key will be none "
        "for every endpoint apart from create",
    )

    class Meta:
        model = MasterAPIKey
        fields = (
            "prefix",
            "created",
            "name",
            "revoked",
            "expiry_date",
            "organisation",
            "key",
        )
        read_only_fields = ("prefix", "created", "key")

    def create(self, validated_data):
        obj, key = MasterAPIKey.objects.create_key(**validated_data)
        obj.key = key
        return obj
