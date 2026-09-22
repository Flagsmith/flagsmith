from django.shortcuts import get_object_or_404
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
    FeatureNotFoundError,
)
from features.dependencies.permissions import check_manage_permissions
from features.dependencies.services import create_flag_dependency
from features.dependencies.types import DependencyEdge
from features.models import Feature


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
        environment = get_object_or_404(Environment, api_key=environment_api_key)
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
