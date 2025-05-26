from typing import Any

import requests
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from webhooks.webhooks import WebhookType

from .permissions import TriggerSampleWebhookPermission
from .webhooks import send_test_request_to_webhook


class WebhookViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, TriggerSampleWebhookPermission]

    @action(detail=False, methods=["POST"])
    def test(self, request: Request) -> Response:
        secret: str | None = request.data.get(
            "secret",
        )
        scope: dict[str, Any] = request.data.get("scope", {})
        webhook_url: str = request.data.get("webhookUrl", "")
        scopeType: str = scope.get("type", "")
        if not all([webhook_url, scopeType]):
            return Response(
                {"detail": "webhookUrl is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            webhook_type = (
                WebhookType.ORGANISATION
                if scopeType == "organisation"
                else WebhookType.ENVIRONMENT
            )
            response = send_test_request_to_webhook(webhook_url, secret, webhook_type)
            if response.status_code != 200:
                return Response(
                    {
                        "detail": "Webhook returned invalid status",
                        "body": response.text,
                        "status": response.status_code,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "detail": "Webhook test successful",
                    "status": response.status_code,
                },
                status=status.HTTP_200_OK,
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {
                    "detail": "Could not connect to webhook URL",
                    "body": str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
