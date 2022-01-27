from rest_framework import serializers


class WebhookSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=["FLAG_UPDATED", "AUDIT_LOG_CREATED"])
    data = serializers.DictField()


class WebhookURLSerializer(serializers.Serializer):
    url = serializers.URLField()
