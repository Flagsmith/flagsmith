from rest_framework import serializers

from .models import DataDogConfiguration


class DataDogConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDogConfiguration
        fields = ("id", "base_url", "api_key")
