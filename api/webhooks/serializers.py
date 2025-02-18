from rest_framework import serializers


class WebhookSerializer(serializers.Serializer):  # type: ignore[type-arg]
    event_type = serializers.ChoiceField(choices=["FLAG_UPDATED", "AUDIT_LOG_CREATED"])
    data = serializers.DictField()  # type: ignore[assignment]


class WebhookURLSerializer(serializers.Serializer):  # type: ignore[type-arg]
    url = serializers.URLField()
