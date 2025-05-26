from rest_framework import serializers


class WebhookSerializer(serializers.Serializer):  # type: ignore[type-arg]
    event_type = serializers.ChoiceField(choices=["FLAG_UPDATED", "AUDIT_LOG_CREATED"])
    data = serializers.DictField()  # type: ignore[assignment]


class WebhookURLSerializer(serializers.Serializer):  # type: ignore[type-arg]
    url = serializers.URLField()


class ScopeSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=["organisation", "environment"])


class TestWebhookSerializer(serializers.Serializer):
    webhookUrl = serializers.URLField(required=True)
    scope = ScopeSerializer(required=True)
    secret = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TestWebhookSuccessResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    status = serializers.IntegerField(default=200)


class TestWebhookErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    status = serializers.IntegerField()
    body = serializers.CharField(required=False, allow_blank=True, allow_null=True)
