from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
import requests

from .webhooks import send_test_request_to_webhook

class WebhookViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["POST"])
    def test(self, request: Request) -> Response:
        secret = request.data.get("secret")
        payload = request.data.get("payload")
        webhook_url = request.data.get("webhookUrl")
        if not all([payload, webhook_url]):
            return Response(
                {"detail": "payload, and webhookUrl are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            response = send_test_request_to_webhook(webhook_url, secret, payload)
            if response.status_code >= 400:
                return Response(
                    {"detail": f"Webhook returned error status: {response.status_code}{', ' + response.text if response.text else ''}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            return Response(
                {"detail": f"Webhook test successful. Response status: {response.status_code}"},
                status=status.HTTP_200_OK,
            )
        except requests.exceptions.RequestException as e:
            return Response(
                {"detail": f"Could not connect to webhook URL: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )