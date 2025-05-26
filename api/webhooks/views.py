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
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    TestWebhookSerializer,
    TestWebhookSuccessResponseSerializer,
    TestWebhookErrorResponseSerializer,
)


class WebhookViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, TriggerSampleWebhookPermission]

    @swagger_auto_schema(
        request_body=TestWebhookSerializer,
        responses={
            200: TestWebhookSuccessResponseSerializer(),
            400: TestWebhookErrorResponseSerializer(),
        },
        method="post",
    )
    @action(
        detail=False,
        url_path="test",
        methods=["POST"],
    )
    def test(self, request: Request) -> Response:
        serializer = TestWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        secret = data.get("secret")
        webhook_url = data["webhookUrl"]
        scope_type = data.get("scope", {}).get("type")
        try:
            webhook_type = (
                WebhookType.ORGANISATION
                if scope_type == "organisation"
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
