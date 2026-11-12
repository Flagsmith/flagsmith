from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):  # type: ignore[type-arg]
    message = serializers.CharField()
