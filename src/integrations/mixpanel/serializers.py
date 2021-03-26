from rest_framework import serializers

from integrations.mixpanel.models import MixpanelConfiguration


class MixpanelConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MixpanelConfiguration
        fields = ("id", "api_key")
