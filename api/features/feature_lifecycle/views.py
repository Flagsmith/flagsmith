import structlog
from common.environments.permissions import VIEW_ENVIRONMENT
from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.models import Environment
from features.feature_lifecycle.serializers import (
    FeatureLifecycleCountsSerializer,
)
from features.feature_lifecycle.services import (
    annotate_feature_queryset_with_lifecycle_stage,
)
from features.feature_lifecycle.types import LifecycleStage

logger = structlog.get_logger("feature_lifecycle")


class FeatureLifecycleCountsAPIView(APIView):
    """Count of features in each lifecycle stage for a project"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["mcp"],
        operation_id="get_feature_lifecycle_counts",
        description=(
            "Retrieves the count of features in each lifecycle stage "
            "for the specified environment."
        ),
        responses={200: FeatureLifecycleCountsSerializer},
    )
    def get(self, request: Request, environment_pk: int) -> Response:
        environment = get_object_or_404(Environment, pk=environment_pk)
        if not request.user.has_environment_permission(VIEW_ENVIRONMENT, environment):  # type: ignore[union-attr]
            return Response(status=403)

        features = annotate_feature_queryset_with_lifecycle_stage(
            environment.project.features.all(),
            environment,
        )

        counts = features.values("lifecycle_stage").annotate(count=Count("pk"))  # type: ignore[misc]
        summary: dict[LifecycleStage, int] = {stage: 0 for stage in LifecycleStage}
        for stage_count in counts:
            summary[stage_count["lifecycle_stage"]] = stage_count["count"]

        logger.info(
            "summarised",
            organisation__id=environment.project.organisation_id,
            environment__id=environment.pk,
        )

        return Response(summary)
