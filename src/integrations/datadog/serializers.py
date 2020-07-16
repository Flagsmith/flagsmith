from rest_framework import serializers

from integrations.datadog.models import DataDogConfiguration


class DataDogConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDogConfiguration
        fields = ('base_url', 'api_key')
