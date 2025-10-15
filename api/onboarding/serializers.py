from rest_framework import serializers


class SelfHostedOnboardingSupportSendRequestSerializer(serializers.Serializer):  # type: ignore[type-arg]
    hubspotutk = serializers.CharField(required=False, allow_blank=True)


class SelfHostedOnboardingReceiveSupportSerializer(serializers.Serializer):  # type: ignore[type-arg]
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    hubspot_cookie = serializers.CharField(required=False, allow_blank=True)
