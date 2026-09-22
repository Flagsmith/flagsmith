from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.types import AuthenticatedRequest
from environments.models import Environment
from features.dependencies.exceptions import (
    DependencyConflictDetail,
    DependencyErrorDetail,
    EnvironmentNotFoundError,
    FeatureNotFoundError,
)
from features.dependencies.permissions import check_manage_permissions
from features.dependencies.services import (
    create_flag_dependency,
    list_flag_dependencies,
    list_flag_dependents,
)
from features.dependencies.types import DependencyEdge, DependencyList
from features.future.permissions import check_read_permissions
from features.models import Feature


def _get_environment(environment_api_key: str) -> Environment:
    try:
        return Environment.objects.get(api_key=environment_api_key)  # type: ignore[no-any-return]
    except Environment.DoesNotExist:
        raise EnvironmentNotFoundError(environment_api_key) from None


def _get_feature(environment: Environment, feature_id: int) -> Feature:
    try:
        return Feature.objects.get(  # type: ignore[no-any-return]
            id=feature_id, project_id=environment.project_id
        )
    except Feature.DoesNotExist:
        raise FeatureNotFoundError(feature_id) from None


class FeatureDependencyAPIView(APIView):
    """Manage a feature's dependency on another feature in an environment."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            201: DependencyEdge,
            400: PolymorphicProxySerializer(
                component_name="DependencyRefusedDetail",
                serializers=[DependencyErrorDetail, DependencyConflictDetail],  # type: ignore[list-item]
                resource_type_field_name=None,
            ),
            403: DependencyErrorDetail,
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
        environment = _get_environment(environment_api_key)
        check_manage_permissions(request.user, environment)
        feature = _get_feature(environment, feature_id)
        prerequisite_feature = _get_feature(environment, prerequisite_feature_id)
        return Response(
            create_flag_dependency(
                environment=environment,
                feature=feature,
                prerequisite_feature=prerequisite_feature,
                author=request.user,
            ),
            status=status.HTTP_201_CREATED,
        )


class FeatureDependenciesAPIView(APIView):
    """List the features a feature depends on in an environment."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: DependencyList, 404: DependencyErrorDetail},
        description="List the features the feature depends on in the environment.",
    )
    def get(
        self,
        request: AuthenticatedRequest,
        environment_api_key: str,
        feature_id: int,
    ) -> Response:
        environment = _get_environment(environment_api_key)
        check_read_permissions(request.user, environment)
        feature = _get_feature(environment, feature_id)
        return Response(
            list_flag_dependencies(environment=environment, feature=feature)
        )


class FeatureDependentsAPIView(APIView):
    """List the features depending on a feature in an environment."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: DependencyList, 404: DependencyErrorDetail},
        description="List the features depending on the feature in the environment.",
    )
    def get(
        self,
        request: AuthenticatedRequest,
        environment_api_key: str,
        feature_id: int,
    ) -> Response:
        environment = _get_environment(environment_api_key)
        check_read_permissions(request.user, environment)
        feature = _get_feature(environment, feature_id)
        return Response(list_flag_dependents(environment=environment, feature=feature))
