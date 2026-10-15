from functools import lru_cache

from django.conf import settings
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.types import APIErrorDetail, AuthenticatedRequest
from environments.services import get_environment
from features.dependencies.exceptions import (
    ChangeRequestAlreadyCommittedError,
    ChangeRequestApprovedError,
    ChangeRequestDisabledError,
    ChangeRequestNotFoundError,
    ChangeRequestPermissionDeniedError,
    DependencyConflictDetail,
    FeatureVersioningDisabledError,
)
from features.dependencies.permissions import check_manage_permissions
from features.dependencies.serializers import ChangeRequestReferenceSerializer
from features.dependencies.services import (
    create_flag_dependency,
    delete_flag_dependency,
    list_flag_dependencies,
    list_flag_dependents,
)
from features.dependencies.types import DependencyEdge, DependencyList
from features.future.permissions import check_read_permissions
from features.services import get_feature
from features.workflows.core.models import ChangeRequest


def _ensure_change_request_is_open(change_request: ChangeRequest) -> None:
    if change_request.has_approvals():
        raise ChangeRequestApprovedError()


@lru_cache(maxsize=1)
def _get_change_request(
    request: AuthenticatedRequest, environment_api_key: str
) -> ChangeRequest | None:
    if not settings.WORKFLOWS_LOGIC_INSTALLED:
        return None
    if "change_request" not in request.query_params:
        return None
    serializer = ChangeRequestReferenceSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    environment = get_environment(environment_api_key)
    check_read_permissions(request.user, environment)
    if not environment.is_workflow_enabled:
        raise ChangeRequestDisabledError()
    if not environment.use_v2_feature_versioning:
        raise FeatureVersioningDisabledError()
    try:
        change_request: ChangeRequest = ChangeRequest.objects.get(
            environment=environment,
            id=serializer.validated_data["change_request"],
        )
    except ChangeRequest.DoesNotExist:
        raise ChangeRequestNotFoundError()
    if change_request.is_committed:
        raise ChangeRequestAlreadyCommittedError()
    return change_request


class _FeatureDependencyBaseAPIView(APIView):
    request: AuthenticatedRequest

    def check_permissions(self, request: Request) -> None:
        super().check_permissions(request)
        if _get_change_request(self.request, self.kwargs["environment_api_key"]):
            from workflows_logic.permissions import CreateChangeRequestPermission

            if not CreateChangeRequestPermission().has_permission(request, self):
                raise ChangeRequestPermissionDeniedError()


class FeaturePrerequisiteAPIView(_FeatureDependencyBaseAPIView):
    """Manage a feature's dependency on another feature in an environment."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            201: DependencyEdge,
            400: PolymorphicProxySerializer(
                component_name="DependencyRefusedDetail",
                serializers=[APIErrorDetail, DependencyConflictDetail],  # type: ignore[list-item]
                resource_type_field_name=None,
            ),
            403: APIErrorDetail,
        },
        description="Make the feature depend on the prerequisite feature being enabled.",
    )
    def post(
        self,
        request: AuthenticatedRequest,
        environment_api_key: str,
        feature_id: int,
        prerequisite_feature_id: int,
    ) -> Response:
        environment = get_environment(environment_api_key)
        if change_request := _get_change_request(request, environment_api_key):
            _ensure_change_request_is_open(change_request)
        else:
            check_manage_permissions(request.user, environment)
        feature = get_feature(environment, feature_id)
        prerequisite_feature = get_feature(environment, prerequisite_feature_id)
        return Response(
            create_flag_dependency(
                environment=environment,
                feature=feature,
                prerequisite_feature=prerequisite_feature,
                author=request.user,
                change_request=change_request,
            ),
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        responses={
            204: None,
            403: APIErrorDetail,
            404: APIErrorDetail,
        },
        description="Stop the feature depending on the prerequisite feature.",
    )
    def delete(
        self,
        request: AuthenticatedRequest,
        environment_api_key: str,
        feature_id: int,
        prerequisite_feature_id: int,
    ) -> Response:
        environment = get_environment(environment_api_key)
        if change_request := _get_change_request(request, environment_api_key):
            _ensure_change_request_is_open(change_request)
        else:
            check_manage_permissions(request.user, environment)
        feature = get_feature(environment, feature_id)
        prerequisite_feature = get_feature(environment, prerequisite_feature_id)
        delete_flag_dependency(
            environment=environment,
            feature=feature,
            prerequisite_feature=prerequisite_feature,
            author=request.user,
            change_request=change_request,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FeatureDependenciesAPIView(_FeatureDependencyBaseAPIView):
    """List the features a feature depends on in an environment."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: DependencyList, 404: APIErrorDetail},
        description="List the features the feature depends on in the environment.",
    )
    def get(
        self,
        request: AuthenticatedRequest,
        environment_api_key: str,
        feature_id: int,
    ) -> Response:
        environment = get_environment(environment_api_key)
        check_read_permissions(request.user, environment)
        feature = get_feature(environment, feature_id)
        return Response(
            list_flag_dependencies(
                environment=environment,
                feature=feature,
                change_request=_get_change_request(request, environment_api_key),
            )
        )


class FeatureDependentsAPIView(_FeatureDependencyBaseAPIView):
    """List the features depending on a feature in an environment."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: DependencyList, 404: APIErrorDetail},
        description="List the features depending on the feature in the environment.",
    )
    def get(
        self,
        request: AuthenticatedRequest,
        environment_api_key: str,
        feature_id: int,
    ) -> Response:
        environment = get_environment(environment_api_key)
        check_read_permissions(request.user, environment)
        feature = get_feature(environment, feature_id)
        return Response(
            list_flag_dependents(
                environment=environment,
                feature=feature,
                change_request=_get_change_request(request, environment_api_key),
            )
        )
