from rest_framework import serializers


class SelfHostedOnboardingSupportRequestSerializer(serializers.Serializer):  # type: ignore[type-arg]
    hubspotutk = serializers.CharField(required=False, allow_blank=True)


class SelfHostedOnboardingSupportSerializer(serializers.Serializer):  # type: ignore[type-arg]
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    hubspotutk = serializers.CharField(required=False, allow_blank=True)
