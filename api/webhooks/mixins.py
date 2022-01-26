from contextlib import suppress

import requests
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import TriggerSampleWebhookPermission
from .serializers import WebhookURLSerializer
from .webhooks import get_webhook_model, trigger_sample_webhook


class TriggerSampleWebhookMixin:
    webhook_type = None

    @action(
        detail=False,
        methods=["POST"],
        url_path="test",
        permission_classes=[IsAuthenticated, TriggerSampleWebhookPermission],
    )
    def trigger_sample_webhook(self, request, **kwargs):
        serializer = WebhookURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        webhook_model = get_webhook_model(self.webhook_type)
        webhook = webhook_model(url=serializer.validated_data["url"])

        with suppress(requests.exceptions.ConnectionError):
            response = trigger_sample_webhook(webhook, self.webhook_type)
            return Response({"message": f"Request returned {response.status_code}"})
        return Response({"message": "Request failed with connection error"})
