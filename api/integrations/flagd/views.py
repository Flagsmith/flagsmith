import hashlib
import json
import time
from datetime import datetime
from typing import Optional

import structlog
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.http import condition
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions
from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from integrations.common.views import ProjectIntegrationBaseViewSet
from integrations.flagd.constants import FLAGD_TRANSLATOR_VERSION
from integrations.flagd.diagnostics import diagnose_environment
from integrations.flagd.metrics import (
    flagsmith_flagd_document_build_seconds,
    flagsmith_flagd_document_size_bytes,
    flagsmith_flagd_sync_requests_total,
)
from integrations.flagd.models import (
    FlagdProjectConfiguration,
    is_flagd_enabled_for_project,
)
from integrations.flagd.serializers import FlagdProjectConfigurationSerializer
from integrations.flagd.services import build_flagd_document


def _require_flagd_enabled(environment) -> None:  # type: ignore[no-untyped-def]
    """
    Both the sync and diagnostics endpoints are opt-in per project.
    Raises ``NotFound`` (404) rather than ``PermissionDenied`` so a
    client probing without authorization can tell the integration
    simply isn't configured.
    """
    if not is_flagd_enabled_for_project(environment.project_id):
        raise NotFound(
            "flagd integration is not enabled for this project."
        )

logger = structlog.get_logger("flagd_sync")


def _effective_last_modified(environment) -> Optional[datetime]:  # type: ignore[no-untyped-def]
    """
    Return the timestamp at which the flagd document for ``environment``
    last *effectively* changed — accounting for scheduled feature-state
    changes that go live without bumping ``environment.updated_at``.

    Considers three signals and returns the latest:
      - ``environment.updated_at`` (covers direct edits)
      - the most recent ``FeatureState.live_from`` <= now in the env
        (covers v1 versioning's scheduled state transitions)
      - the most recent ``EnvironmentFeatureVersion.live_from`` <= now
        in the env (covers v2 versioning's scheduled publishes)
    """
    candidates: list[datetime] = []
    if environment.updated_at:
        candidates.append(environment.updated_at)

    now = timezone.now()
    v1_live_from = (
        FeatureState.objects.filter(
            environment_id=environment.id,
            live_from__isnull=False,
            live_from__lte=now,
        )
        .order_by("-live_from")
        .values_list("live_from", flat=True)
        .first()
    )
    if v1_live_from:
        candidates.append(v1_live_from)

    v2_live_from = (
        EnvironmentFeatureVersion.objects.filter(
            environment_id=environment.id,
            published_at__isnull=False,
            live_from__lte=now,
        )
        .order_by("-live_from")
        .values_list("live_from", flat=True)
        .first()
    )
    if v2_live_from:
        candidates.append(v2_live_from)

    return max(candidates) if candidates else None


def _get_last_modified(request: Request) -> Optional[datetime]:
    environment = getattr(request, "environment", None)
    if environment is None:
        return None
    return _effective_last_modified(environment)


def _get_etag(request: Request) -> Optional[str]:
    environment = getattr(request, "environment", None)
    if environment is None:
        return None
    last_modified = _effective_last_modified(environment)
    if last_modified is None:
        return None
    raw = (
        f"{environment.api_key}:"
        f"{last_modified.isoformat()}:"
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
        _require_flagd_enabled(environment)
        start = time.perf_counter()
        document = build_flagd_document(environment)
        flagsmith_flagd_document_build_seconds.observe(time.perf_counter() - start)
        warnings_count = len(document.get("metadata", {}).get("flagsmith.warnings", []))
        flagsmith_flagd_sync_requests_total.labels(status="200").inc()
        flagsmith_flagd_document_size_bytes.observe(len(json.dumps(document).encode()))
        logger.info(
            "document.served",
            environment__id=environment.id,
            warnings__count=warnings_count,
        )
        return Response(document)


@extend_schema(tags=["sdk"])
class FlagdDiagnosticsAPIView(APIView):
    """
    Reports translation warnings for the current environment without
    serving the sync document. Operators curl this to audit an
    environment (type mismatches, REGEX skipped, identity-override cap
    hit, …) before promoting to a flagd-consumer-facing change.
    """

    permission_classes = (EnvironmentKeyPermissions,)
    throttle_classes = []

    def get_authenticators(self):  # type: ignore[no-untyped-def]
        return [EnvironmentKeyAuthentication(required_key_prefix="ser.")]

    @extend_schema(operation_id="sdk_v1_flagd_diagnostics")
    def get(self, request: Request) -> Response:
        environment = request.environment
        _require_flagd_enabled(environment)
        report = diagnose_environment(environment)
        logger.info(
            "diagnostics.served",
            environment__id=environment.id,
            features_with_warnings=report["summary"]["featuresWithWarnings"],
            total_warnings=report["summary"]["totalWarnings"],
        )
        return Response(report)


@extend_schema(tags=["integrations"])
class FlagdProjectConfigurationViewSet(ProjectIntegrationBaseViewSet):
    """
    Admin toggle for the flagd integration, scoped to one project.

    Inherits the standard Flagsmith ``ProjectIntegrationBaseViewSet``
    used by every other integration (datadog, grafana, etc.). That base
    class wires up the project-nested permission model, the
    "one-config-per-project" guard on create, and the project filter
    on the queryset. The plugin keeps full ownership of the model,
    serializer, and gating semantics.
    """

    serializer_class = FlagdProjectConfigurationSerializer
    pagination_class = None
    model_class = FlagdProjectConfiguration
