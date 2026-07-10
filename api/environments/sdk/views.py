from datetime import datetime
from typing import Optional

from django.utils.decorators import method_decorator
from django.views.decorators.http import condition
from drf_spectacular.utils import OpenApiParameter, extend_schema
from flagsmith_schemas.api import V1EnvironmentDocumentResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.constants import FLAGSMITH_UPDATED_AT_HEADER
from environments.authentication import (
    EnvironmentKeyAuthentication,
)
from environments.models import Environment
from environments.permissions.permissions import EnvironmentKeyPermissions


def _is_include_scheduled_requested(request: Request) -> bool:
    # Opt-in query param for `scheduled_change` data.
    return request.GET.get("include_scheduled", "").lower() in ("1", "true", "yes")


def get_last_modified(request: Request) -> datetime | None:
    # A schedule maturing (`live_from` passing) doesn't touch
    # `environment.updated_at` — nothing is saved when time simply
    # elapses. Requests that opt into `scheduled_change` data therefore can't
    # rely on this field to decide freshness, and worse, a client that has a
    # cached body from *before* it started opting in could otherwise get a
    # 304 short-circuit here and keep reusing that stale, scheduled-change-free
    # body forever. Returning None tells Django's `condition()` there is no
    # known last-modified value, so it always falls through to `get()` instead.
    # Trade-off: this disables the 304 short-circuit for every
    # `include_scheduled=True` request (each one always executes `get()` in
    # full), in exchange for guaranteed freshness rather than a cheap-but-stale
    # response.
    if _is_include_scheduled_requested(request):
        return None
    updated_at: Optional[datetime] = request.environment.updated_at
    return updated_at


@extend_schema(tags=["sdk"])
class SDKEnvironmentAPIView(APIView):
    permission_classes = (EnvironmentKeyPermissions,)
    throttle_classes = []

    def get_authenticators(self):  # type: ignore[no-untyped-def]
        return [EnvironmentKeyAuthentication(required_key_prefix="ser.")]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="include_scheduled",
                type=bool,
                required=False,
                description=(
                    "Opt-in. When true, each feature state in "
                    "the response carries an additional `scheduled_change` "
                    "field describing its next not-yet-live version, if any. "
                    "Defaults to false, in which case the response shape is "
                    "unchanged. Note: not every scheduled-change shape is "
                    "currently surfaced (e.g. v2 segment overrides via the "
                    "versioning flow, brand-new segment overrides, scheduled "
                    "deletions, and multivariate weight changes)."
                ),
            ),
        ],
        responses={200: V1EnvironmentDocumentResponse},
        operation_id="sdk_v1_environment_document",
    )
    @method_decorator(condition(last_modified_func=get_last_modified))
    def get(self, request: Request) -> Response:
        """
        Retrieve the environment document.
        Used by SDKs in local evaluation mode, and Edge Proxy.
        """
        environment_document = Environment.get_environment_document(
            request.environment.api_key,
            include_scheduled=_is_include_scheduled_requested(request),
        )
        updated_at = self.request.environment.updated_at
        return Response(
            environment_document,
            headers={FLAGSMITH_UPDATED_AT_HEADER: updated_at.timestamp()},
        )
