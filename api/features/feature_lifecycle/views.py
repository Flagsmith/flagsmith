from datetime import timedelta

from common.environments.permissions import VIEW_ENVIRONMENT
from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_analytics.services import get_features_in_use
from environments.models import Environment
from features.feature_lifecycle.types import LifecycleStage
from projects.code_references.services import get_feature_flags_in_latest_scan
from projects.tags.models import Tag, TagType


class FeatureLifecycleCountsAPIView(APIView):
    """Count of features in each lifecycle stage for a project"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, environment_pk: int) -> Response:
        environment = get_object_or_404(Environment, pk=environment_pk)
        if not request.user.has_environment_permission(VIEW_ENVIRONMENT, environment):
            return Response(status=403)

        days_until_stale = environment.project.stale_flags_limit_days
        usage_window = timezone.now() - timedelta(days=days_until_stale)

        features_in_code = get_feature_flags_in_latest_scan(environment.project)
        features_in_use = get_features_in_use(environment, since=usage_window)

        features = environment.project.features.only("name").annotate(
            has_code_references=Exists(
                features_in_code.filter(pk=OuterRef("pk")),
            ),
            has_recent_usage=(
                Exists(features_in_use.filter(pk=OuterRef("pk")))
                if features_in_use is not None
                else Cast(Value(None), output_field=BooleanField())
            ),
            has_permanent_tag=Exists(
                Tag.objects.filter(feature=OuterRef("pk"), is_permanent=True),
            ),
            has_stale_tag=Exists(
                Tag.objects.filter(feature=OuterRef("pk"), type=TagType.STALE),
            ),
        )

        summary: dict[LifecycleStage, int] = features.aggregate(
            **{
                LifecycleStage.NEW: Count(
                    "pk",
                    filter=Q(
                        has_code_references=False,
                        has_permanent_tag=False,
                        has_stale_tag=False,
                    ),
                ),
                LifecycleStage.LIVE: Count(
                    "pk",
                    filter=Q(
                        has_code_references=True,
                        has_permanent_tag=False,
                        has_stale_tag=False,
                    ),
                ),
                LifecycleStage.STALE: Count(
                    "pk",
                    filter=Q(
                        has_code_references=True,
                        has_permanent_tag=False,
                        has_stale_tag=True,
                    ),
                ),
                LifecycleStage.PERMANENT: Count(
                    "pk",
                    filter=Q(
                        has_permanent_tag=True,
                    ),
                ),
                LifecycleStage.NEEDS_MONITORING: Count(
                    "pk",
                    filter=Q(
                        has_code_references=False,
                        has_permanent_tag=False,
                        has_stale_tag=True,
                        has_recent_usage=True,
                    ),
                ),
                LifecycleStage.TO_REMOVE: Count(
                    "pk",
                    filter=Q(
                        has_code_references=False,
                        has_permanent_tag=False,
                        has_stale_tag=True,
                        has_recent_usage=False,
                    ),
                ),
            }
        )

        return Response(summary)
