from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from environments.models import Environment

from .permissions import EnvironmentUpdateFeatureStatePermission
from .serializers import (
    DeleteSegmentOverrideSerializer,
    UpdateFlagSerializer,
    UpdateFlagV2Serializer,
)


def _check_workflow_not_enabled(environment: Environment) -> None:
    if environment.is_workflow_enabled:
        raise PermissionDenied(
            "This endpoint cannot be used when change requests are enabled. "
            "Use the change request workflow instead."
        )


@extend_schema(
    summary="Update single feature state",
    description="""
    **EXPERIMENTAL ENDPOINT** - Subject to change without notice.

    Updates a single feature state within an environment. You can update either:
    - The environment default state (when no segment is specified)
    - A specific segment override (when segment.id is provided)

    **Feature Identification:**
    - Use `feature.name` OR `feature.id` (mutually exclusive)

    **Value Format:**
    - The `value` field is always a string representation
    - The `type` field tells the server how to parse it
    - Available types: integer, string, boolean
    - Examples:
      - `{"type": "integer", "value": "42"}`
      - `{"type": "boolean", "value": "true"}`
      - `{"type": "string", "value": "hello"}`

    **Segment Priority:**
    - Optional `segment.priority` field controls ordering
    - If field value is null or the field is omitted, lowest priority is assumed
    """,
    parameters=[
        OpenApiParameter(
            name="environment_key",
            location=OpenApiParameter.PATH,
            description="The environment API key",
            type=str,
            required=True,
        )
    ],
    request=UpdateFlagSerializer,
    responses={204: None},
    tags=["experimental"],
)
@api_view(http_method_names=["POST"])
@permission_classes([IsAuthenticated, EnvironmentUpdateFeatureStatePermission])
def update_flag_v1(request: Request, environment_key: str) -> Response:
    environment = Environment.objects.get(api_key=environment_key)
    _check_workflow_not_enabled(environment)

    serializer = UpdateFlagSerializer(
        data=request.data,
        context={"request": request, "environment": environment},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Update multiple feature states",
    description="""
    **EXPERIMENTAL ENDPOINT** - Subject to change without notice.

    Updates multiple feature states in a single request. This endpoint allows
    you to configure an entire feature (environment default + all segment overrides)
    in one operation.

    **What You Can Update:**
    - Environment default state (required)
    - Multiple segment overrides (optional)
    - Priority ordering for each segment

    **Feature Identification:**
    - Use `feature.name` OR `feature.id` (mutually exclusive)

    **Value Format:**
    - The `value` field is always a string representation
    - The `type` field tells the server how to parse it
    - Available types: integer, string, boolean
    - Examples:
      - `{"type": "string", "value": "production"}`
      - `{"type": "integer", "value": "100"}`
      - `{"type": "boolean", "value": "false"}`

    **Segment Overrides:**
    - Provide array of segment override configurations
    - Each override must specify: segment_id, enabled, value
    - Optional priority field controls ordering
    - Duplicate segment_id values are not allowed

    """,
    parameters=[
        OpenApiParameter(
            name="environment_key",
            location=OpenApiParameter.PATH,
            description="The environment API key",
            type=str,
            required=True,
        )
    ],
    request=UpdateFlagV2Serializer,
    responses={204: None},
    tags=["experimental"],
)
@api_view(http_method_names=["POST"])
@permission_classes([IsAuthenticated, EnvironmentUpdateFeatureStatePermission])
def update_flag_v2(request: Request, environment_key: str) -> Response:
    environment = Environment.objects.get(api_key=environment_key)
    _check_workflow_not_enabled(environment)

    serializer = UpdateFlagV2Serializer(
        data=request.data,
        context={"request": request, "environment": environment},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Delete segment override",
    description="""
    **EXPERIMENTAL ENDPOINT** - Subject to change without notice.

    Deletes a segment override for a feature in the given environment.

    **Feature Identification:**
    - Use `feature.name` OR `feature.id` (mutually exclusive)
    - Feature must belong to the environment's project

    **Segment Identification:**
    - Use `segment.id` (required)

    The segment override must exist for the given feature/environment combination.
    Returns 400 if the segment override does not exist.
    """,
    parameters=[
        OpenApiParameter(
            name="environment_key",
            location=OpenApiParameter.PATH,
            description="The environment API key",
            type=str,
            required=True,
        )
    ],
    request=DeleteSegmentOverrideSerializer,
    responses={204: None},
    tags=["experimental"],
)
@api_view(http_method_names=["POST"])
@permission_classes([IsAuthenticated, EnvironmentUpdateFeatureStatePermission])
def delete_segment_override(request: Request, environment_key: str) -> Response:
    environment = Environment.objects.get(api_key=environment_key)
    _check_workflow_not_enabled(environment)

    serializer = DeleteSegmentOverrideSerializer(
        data=request.data,
        context={"request": request, "environment": environment},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(status=status.HTTP_204_NO_CONTENT)
