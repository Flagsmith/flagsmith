from rest_framework import serializers

from integrations.heap.models import HeapConfiguration


class HeapConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeapConfiguration
        fields = ("id", "api_key")
