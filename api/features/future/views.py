"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from collections.abc import Mapping

import structlog
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.dataclasses import AuthorData
from core.types import AuthenticatedRequest
from environments.models import Environment
from features.future.exceptions import ChangeRequestsEnabledError
from features.future.permissions import (
    check_read_permissions,
    check_segment_overrides_permissions,
    check_update_permissions,
)
from features.future.serializers import UpdateFlagSerializer
from features.future.services import delete_segment_override, get_flag, update_flag
from features.future.types import UpdateFlagRequest, UpdateFlagResponse
from features.models import Feature

logger = structlog.get_logger("features")


def _get_environment(environment_key: str) -> Environment:
    try:
        return Environment.objects.get(api_key=environment_key)  # type: ignore[no-any-return]
    except Environment.DoesNotExist:
        raise NotFound() from None


def _get_feature(environment: Environment, feature_id: int) -> Feature:
    try:
        return Feature.objects.get(  # type: ignore[no-any-return]
            id=feature_id, project_id=environment.project_id
        )
    except Feature.DoesNotExist:
        raise NotFound() from None


def _check_change_requests_disabled(environment: Environment, feature: Feature) -> None:
    """Refuse to write a flag that can only be changed by a change request."""
    if not environment.is_workflow_enabled:
        return
    api_error = ChangeRequestsEnabledError()
    logger.warning(
        "flag.update_rejected",
        organisation__id=environment.project.organisation_id,
        project__id=environment.project_id,
        environment__id=environment.id,
        feature__id=feature.id,
        reason=api_error.default_code,
    )
    raise api_error


class FlagAPIView(APIView):
    """Read or update what a flag serves in an environment."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=UpdateFlagResponse,
        tags=["experimental"],
        description="Read what the flag serves in the environment.",
    )
    def get(
        self, request: AuthenticatedRequest, environment_key: str, feature_id: int
    ) -> Response:
        environment = _get_environment(environment_key)
        check_read_permissions(request.user, environment)
        feature = _get_feature(environment, feature_id)

        return Response(get_flag(environment=environment, feature=feature))

    @extend_schema(
        request=UpdateFlagRequest,
        responses=UpdateFlagResponse,
        tags=["experimental"],
        description="Update the properties given, leaving the rest as they are.",
    )
    def patch(
        self, request: AuthenticatedRequest, environment_key: str, feature_id: int
    ) -> Response:
        return self._update_flag(request, environment_key, feature_id, replace=False)

    @extend_schema(
        request=UpdateFlagRequest,
        responses=UpdateFlagResponse,
        tags=["experimental"],
        description="Replace the properties given, resetting what they omit.",
    )
    def put(
        self, request: AuthenticatedRequest, environment_key: str, feature_id: int
    ) -> Response:
        return self._update_flag(request, environment_key, feature_id, replace=True)

    def _update_flag(
        self,
        request: AuthenticatedRequest,
        environment_key: str,
        feature_id: int,
        *,
        replace: bool,
    ) -> Response:
        if not isinstance(request.data, Mapping):
            raise ValidationError("Expected an object.")

        environment = _get_environment(environment_key)
        check_update_permissions(request.user, environment, request.data)
        feature = _get_feature(environment, feature_id)
        _check_change_requests_disabled(environment, feature)

        serializer = UpdateFlagSerializer(
            data=request.data,
            context={"feature": feature, "replace": replace},
        )
        serializer.is_valid(raise_exception=True)

        return Response(
            update_flag(
                environment=environment,
                feature=feature,
                changes=serializer.validated_data,
                replace=replace,
                author=AuthorData.from_request(request),
            )
        )


class SegmentOverrideAPIView(APIView):
    """Remove what a flag serves to a segment in an environment."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        # Responds with the flag, like the other methods, rather than no content.
        responses={200: UpdateFlagResponse},
        tags=["experimental"],
        description=(
            "Remove the flag's override for the segment, "
            "leaving the rest of the flag as it is."
        ),
    )
    def delete(
        self,
        request: AuthenticatedRequest,
        environment_key: str,
        feature_id: int,
        segment_id: int,
    ) -> Response:
        environment = _get_environment(environment_key)
        check_segment_overrides_permissions(request.user, environment)
        feature = _get_feature(environment, feature_id)
        _check_change_requests_disabled(environment, feature)

        return Response(
            delete_segment_override(
                environment=environment,
                feature=feature,
                segment_id=segment_id,
                author=AuthorData.from_request(request),
            )
        )
