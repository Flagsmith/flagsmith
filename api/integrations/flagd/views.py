import hashlib
import json
import time
from datetime import datetime
from typing import Optional

import structlog
from django.utils.decorators import method_decorator
from django.views.decorators.http import condition
from drf_spectacular.utils import extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions
from integrations.flagd.constants import FLAGD_TRANSLATOR_VERSION
from integrations.flagd.metrics import (
    flagsmith_flagd_document_build_seconds,
    flagsmith_flagd_document_size_bytes,
    flagsmith_flagd_sync_requests_total,
)
from integrations.flagd.services import build_flagd_document

logger = structlog.get_logger("flagd_sync")


def _get_last_modified(request: Request) -> Optional[datetime]:
    environment = getattr(request, "environment", None)
    if environment is None:
        return None
    return environment.updated_at


def _get_etag(request: Request) -> Optional[str]:
    environment = getattr(request, "environment", None)
    if environment is None or environment.updated_at is None:
        return None
    raw = (
        f"{environment.api_key}:"
        f"{environment.updated_at.isoformat()}:"
        f"{FLAGD_TRANSLATOR_VERSION}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


@extend_schema(tags=["sdk"])
class FlagdSyncAPIView(APIView):
    """
    HTTP sync endpoint consumed by flagd: returns the current
    Flagsmith environment as a flagd flag-definition document.
    """

    permission_classes = (EnvironmentKeyPermissions,)
    throttle_classes = []

    def get_authenticators(self):  # type: ignore[no-untyped-def]
        return [EnvironmentKeyAuthentication(required_key_prefix="ser.")]

    @extend_schema(operation_id="sdk_v1_flagd_sync")
    @method_decorator(
        condition(last_modified_func=_get_last_modified, etag_func=_get_etag)
    )
    def get(self, request: Request) -> Response:
        environment = request.environment
        start = time.perf_counter()
        document = build_flagd_document(environment)
        flagsmith_flagd_document_build_seconds.observe(time.perf_counter() - start)
        warnings_count = len(
            document.get("metadata", {}).get("flagsmith.warnings", [])
        )
        flagsmith_flagd_sync_requests_total.labels(status="200").inc()
        flagsmith_flagd_document_size_bytes.observe(
            len(json.dumps(document).encode())
        )
        logger.info(
            "document.served",
            environment__id=environment.id,
            warnings__count=warnings_count,
        )
        return Response(document)
