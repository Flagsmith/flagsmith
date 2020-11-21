from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    message = serializers.CharField()
