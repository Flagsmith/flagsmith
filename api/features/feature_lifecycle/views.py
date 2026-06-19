from typing import Any

from common.projects.permissions import VIEW_PROJECT
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from features.feature_lifecycle.types import LifecycleStage


class FeatureLifecycleCountsAPIView(APIView):
    """Count of features in each lifecycle stage for a project"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Any, project_pk: int, **kwargs: Any) -> Response:
        project = get_object_or_404(
            request.user.get_permitted_projects(VIEW_PROJECT),
            pk=project_pk,
        )

        summary: dict[LifecycleStage, int] = {}

        features = project.features.all()

        return Response(summary)
