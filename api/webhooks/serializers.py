from rest_framework import serializers

from webhooks.fields import NoSSRFURLField


class WebhookSerializer(serializers.Serializer[None]):
    event_type = serializers.ChoiceField(choices=["FLAG_UPDATED", "AUDIT_LOG_CREATED"])
    data = serializers.DictField()  # type: ignore[assignment]


class WebhookURLSerializer(serializers.Serializer[None]):
    url = NoSSRFURLField()


class ScopeSerializer(serializers.Serializer[None]):
    type = serializers.ChoiceField(choices=["organisation", "environment"])


class TestWebhookSerializer(serializers.Serializer[None]):
    webhook_url = NoSSRFURLField(required=True)
    scope = ScopeSerializer(required=True)
    secret = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class TestWebhookSuccessResponseSerializer(serializers.Serializer[None]):
    detail = serializers.CharField()
    status = serializers.IntegerField(default=200)


class TestWebhookErrorResponseSerializer(serializers.Serializer[None]):
    detail = serializers.CharField()
    status = serializers.IntegerField(
        required=False,
        help_text="HTTP status returned by the webhook, if it responded.",
    )
    body = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    code = serializers.CharField(
        required=False,
        help_text=(
            "Set when the webhook could not be reached: a POSIX error name"
            " (e.g. `ECONNREFUSED`, `ETIMEDOUT`) or a Node.js-style TLS"
            " error code (e.g. `CERT_HAS_EXPIRED`)."
        ),
    )
