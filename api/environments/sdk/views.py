from datetime import datetime
from typing import Optional

from django.utils.decorators import method_decorator
from django.views.decorators.http import condition
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.constants import FLAGSMITH_UPDATED_AT_HEADER
from environments.authentication import (
    EnvironmentKeyAuthentication,
)
from environments.models import Environment
from environments.permissions.permissions import EnvironmentKeyPermissions
from environments.sdk.schemas import SDKEnvironmentDocumentModel


def get_last_modified(request: Request) -> datetime | None:
    updated_at: Optional[datetime] = request.environment.updated_at
    return updated_at


class SDKEnvironmentAPIView(APIView):
    permission_classes = (EnvironmentKeyPermissions,)
    throttle_classes = []

    def get_authenticators(self):  # type: ignore[no-untyped-def]
        return [EnvironmentKeyAuthentication(required_key_prefix="ser.")]

    @swagger_auto_schema(responses={200: SDKEnvironmentDocumentModel})  # type: ignore[misc]
    @method_decorator(condition(last_modified_func=get_last_modified))
    def get(self, request: Request) -> Response:
        environment_document = Environment.get_environment_document(
            request.environment.api_key,
        )
        updated_at = self.request.environment.updated_at
        return Response(
            environment_document,
            headers={FLAGSMITH_UPDATED_AT_HEADER: updated_at.timestamp()},
        )
