from typing import Any

import requests
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

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
        payload: dict[str, Any] | None = request.data.get("payload", {})
        webhook_url: str = request.data.get("webhookUrl", "")
        if not webhook_url:
            return Response(
                {"detail": "webhookUrl is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            assert isinstance(webhook_url, str)
            assert isinstance(payload, dict)
            response = send_test_request_to_webhook(
                webhook_url, secret, scope.get("type")
            )
            if response.status_code != 200:
                return Response(
                    {
                        "detail": "Webhook returned error status",
                        "body": response.text,
                        "code": response.status_code,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {
                    "detail": "Webhook test successful",
                    "code": response.status_code,
                },
                status=status.HTTP_200_OK,
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {"detail": f"Could not connect to webhook URL: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
