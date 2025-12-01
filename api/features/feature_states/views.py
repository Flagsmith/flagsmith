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
    operation_summary="Update single feature state (V1)",
    operation_description="""
    **EXPERIMENTAL ENDPOINT** - Subject to change without notice.

    Updates a single feature state within an environment. You can update either:
    - The environment default state (when no segment is specified)
    - A specific segment override (when segment.id is provided)

    **Feature Identification:**
    - Use `feature.name` OR `feature.id` (mutually exclusive)
    - Feature must belong to the environment's project

    **Value Format:**
    - Always use `string_value` field (value is always a string)
    - The `type` field tells the server how to parse it
    - Available types: integer, string, boolean
    - Examples:
      - `{"type": "integer", "string_value": "42"}`
      - `{"type": "boolean", "string_value": "true"}`
      - `{"type": "string", "string_value": "hello"}`

    **Segment Priority:**
    - Optional `segment.priority` field controls ordering
    - If null/omitted, segment is appended to end
    - Use specific priority value to reorder
    """,
    request_body=UpdateFlagSerializer,
    responses={
        204: openapi.Response(
            description="Feature state updated successfully (no content returned)"
        )
    },
    tags=["Experimental - Feature States"],
)  # type: ignore[misc]
@api_view(http_method_names=["POST"])
@permission_classes([IsAuthenticated, EnvironmentUpdateFeatureStatePermission])
def update_flag_v1(request: Request, environment_id: int) -> Response:
    environment = Environment.objects.get(id=environment_id)
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
    - Feature must belong to the environment's project

    **Value Format:**
    - Always use `string_value` field (value is always a string)
    - The `type` field tells the server how to parse it
    - Available types: integer, string, boolean
    - Examples:
      - `{"type": "string", "string_value": "production"}`
      - `{"type": "integer", "string_value": "100"}`
      - `{"type": "boolean", "string_value": "false"}`

    **Segment Overrides:**
    - Provide array of segment override configurations
    - Each override must specify: segment_id, enabled, value
    - Optional priority field controls ordering
    - Duplicate segment_id values are not allowed

    """,
    request_body=UpdateFlagV2Serializer,
    responses={
        204: openapi.Response(
            description="Feature states updated successfully (no content returned)"
        )
    },
    tags=["Experimental - Feature States"],
)  # type: ignore[misc]
@api_view(http_method_names=["POST"])
@permission_classes([IsAuthenticated, EnvironmentUpdateFeatureStatePermission])
def update_flag_v2(request: Request, environment_id: int) -> Response:
    environment = Environment.objects.get(id=environment_id)
    _check_workflow_not_enabled(environment)

    serializer = UpdateFlagV2Serializer(
        data=request.data,
        context={"request": request, "environment": environment},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(status=status.HTTP_204_NO_CONTENT)
