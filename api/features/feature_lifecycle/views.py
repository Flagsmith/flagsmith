from common.environments.permissions import VIEW_ENVIRONMENT
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.models import Environment
from features.feature_lifecycle.services import (
    annotate_feature_queryset_with_lifecycle_stage,
)
from features.feature_lifecycle.types import LifecycleStage


class FeatureLifecycleCountsAPIView(APIView):
    """Count of features in each lifecycle stage for a project"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, environment_pk: int) -> Response:
        environment = get_object_or_404(Environment, pk=environment_pk)
        if not request.user.has_environment_permission(VIEW_ENVIRONMENT, environment):
            return Response(status=403)

        features = annotate_feature_queryset_with_lifecycle_stage(
            environment.project.features.all(),
            environment,
        )

        counts = features.values("lifecycle_stage").annotate(count=Count("pk"))
        summary: dict[LifecycleStage, int] = {stage: 0 for stage in LifecycleStage}
        for stage_count in counts:
            summary[stage_count["lifecycle_stage"]] = stage_count["count"]

        return Response(summary)
