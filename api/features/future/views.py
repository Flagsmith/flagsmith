"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from collections.abc import Mapping

import structlog
from django.contrib.auth.models import AnonymousUser
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.models import Environment
from features.future.exceptions import ChangeRequestsEnabledError
from features.future.permissions import (
    check_read_permissions,
    check_update_permissions,
)
from features.future.serializers import UpdateFlagSerializer
from features.future.services import get_flag, update_flag
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


class FlagAPIView(APIView):
    """Read or update what a flag serves in an environment."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses=UpdateFlagResponse,
        tags=["experimental"],
        description="Read what the flag serves in the environment.",
    )
    def get(self, request: Request, environment_key: str, feature_id: int) -> Response:
        assert not isinstance(request.user, AnonymousUser)

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
        self, request: Request, environment_key: str, feature_id: int
    ) -> Response:
        return self._update_flag(request, environment_key, feature_id, replace=False)

    @extend_schema(
        request=UpdateFlagRequest,
        responses=UpdateFlagResponse,
        tags=["experimental"],
        description="Replace the properties given, resetting what they omit.",
    )
    def put(self, request: Request, environment_key: str, feature_id: int) -> Response:
        return self._update_flag(request, environment_key, feature_id, replace=True)

    def _update_flag(
        self,
        request: Request,
        environment_key: str,
        feature_id: int,
        *,
        replace: bool,
    ) -> Response:
        assert not isinstance(request.user, AnonymousUser)

        if not isinstance(request.data, Mapping):
            raise ValidationError("Expected an object.")

        environment = _get_environment(environment_key)
        check_update_permissions(request.user, environment, request.data)
        feature = _get_feature(environment, feature_id)

        if environment.is_workflow_enabled:
            logger.warning(
                "flag.update_rejected",
                organisation__id=environment.project.organisation_id,
                project__id=environment.project_id,
                environment__id=environment.id,
                feature__id=feature.id,
                reason="change_requests_enabled",
            )
            raise ChangeRequestsEnabledError()

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
                author=request.user,
            )
        )
