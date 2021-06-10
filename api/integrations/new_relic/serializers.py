from rest_framework import serializers

from .models import NewRelicConfiguration


class NewRelicConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewRelicConfiguration
        fields = ("id", "base_url", "api_key", "app_id")
