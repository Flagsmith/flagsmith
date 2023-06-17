from rest_framework import serializers

from webhooks.webhooks import WebhookEventType


class WebhookSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(
        choices=[event.name for event in WebhookEventType]
    )
    data = serializers.DictField()


class WebhookURLSerializer(serializers.Serializer):
    url = serializers.URLField()
