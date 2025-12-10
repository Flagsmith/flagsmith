from drf_yasg import openapi  # type: ignore[import-untyped]
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from environments.models import Environment

from .permissions import EnvironmentUpdateFeatureStatePermission
from .serializers import UpdateFlagSerializer, UpdateFlagV2Serializer


def _check_workflow_not_enabled(environment: Environment) -> None:
    if environment.is_workflow_enabled:
        raise PermissionDenied(
            "This endpoint cannot be used when change requests are enabled. "
            "Use the change request workflow instead."
        )


@swagger_auto_schema(
    method="post",
    operation_summary="Update single feature state",
    operation_description="""
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
    manual_parameters=[
        openapi.Parameter(
            "environment_key",
            openapi.IN_PATH,
            description="The environment API key",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    request_body=UpdateFlagSerializer,
    responses={
        204: openapi.Response(
            description="Feature state updated successfully (no content returned)"
        )
    },
    tags=["experimental"],
)  # type: ignore[misc]
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


@swagger_auto_schema(
    method="post",
    operation_summary="Update multiple feature states",
    operation_description="""
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
    manual_parameters=[
        openapi.Parameter(
            "environment_key",
            openapi.IN_PATH,
            description="The environment API key",
            type=openapi.TYPE_STRING,
            required=True,
        )
    ],
    request_body=UpdateFlagV2Serializer,
    responses={
        204: openapi.Response(
            description="Feature states updated successfully (no content returned)"
        )
    },
    tags=["experimental"],
)  # type: ignore[misc]
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
