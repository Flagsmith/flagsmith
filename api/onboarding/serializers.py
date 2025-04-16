from rest_framework import serializers


class SelfHostedOnboardingSupportSerializer(serializers.Serializer):  # type: ignore[type-arg]
    organisation_name = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
