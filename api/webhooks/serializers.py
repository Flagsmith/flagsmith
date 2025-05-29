from rest_framework import serializers


class WebhookSerializer(serializers.Serializer[None]):
    event_type = serializers.ChoiceField(choices=["FLAG_UPDATED", "AUDIT_LOG_CREATED"])
    data = serializers.DictField()  # type: ignore[assignment]


class WebhookURLSerializer(serializers.Serializer[None]):
    url = serializers.URLField()


class ScopeSerializer(serializers.Serializer[None]):
    type = serializers.ChoiceField(choices=["organisation", "environment"])


class TestWebhookSerializer(serializers.Serializer[None]):
    webhook_url = serializers.URLField(required=True)
    scope = ScopeSerializer(required=True)
    secret = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TestWebhookSuccessResponseSerializer(serializers.Serializer[None]):
    detail = serializers.CharField()
    status = serializers.IntegerField(default=200)


class TestWebhookErrorResponseSerializer(serializers.Serializer[None]):
    detail = serializers.CharField()
    status = serializers.IntegerField()
    body = serializers.CharField(required=False, allow_blank=True, allow_null=True)
