import hmac
from typing import cast

import structlog
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from integrations.gitlab.models import GitLabWebhook
from integrations.gitlab.services import apply_tag_for_event
from integrations.gitlab.types import GitLabWebhookPayload

logger = structlog.get_logger("gitlab")


@api_view(["POST"])
@permission_classes([AllowAny])
def gitlab_webhook(request: Request, webhook_uuid: str) -> Response:
    try:
        webhook = GitLabWebhook.objects.select_related(
            "gitlab_configuration__project"
        ).get(uuid=webhook_uuid)
    except GitLabWebhook.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    token = request.headers.get("X-Gitlab-Token", "")
    if not hmac.compare_digest(token, webhook.secret):
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    apply_tag_for_event(
        webhook=webhook,
        payload=cast(GitLabWebhookPayload, request.data),
    )
    return Response(status=status.HTTP_200_OK)
