from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import TriggerSampleWebhookPermission
from .serializers import WebhookURLSerializer


class TriggerSampleWebhookMixin:
    webhook_model = None
    sample_trigger_method = None

    @action(
        detail=False,
        methods=["POST"],
        url_path="test",
        permission_classes=[IsAuthenticated, TriggerSampleWebhookPermission],
    )
    def trigger_sample_webhook(self, request, **kwargs):
        serializer = WebhookURLSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        webhook = self.webhook_model(url=serializer.validated_data["url"])
        response = self.sample_trigger_method(webhook)
        message = (
            f"Request returned {response.status_code}"
            if response
            else "Request failed with connection error"
        )
        return Response({"message": message})
