from rest_framework import serializers

from integrations.amplitude.models import AmplitudeConfiguration


class AmplitudeConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmplitudeConfiguration
        fields = ('api_key')
