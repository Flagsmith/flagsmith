from typing import Any

import structlog
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, response, status
from rest_framework.request import Request

from features.models import Feature
from projects.code_references.permissions import (
    SubmitFeatureFlagCodeReferences,
    ViewFeatureFlagCodeReferences,
)
from projects.code_references.serializers import (
    FeatureFlagCodeReferencesRepositorySummarySerializer,
    FeatureFlagCodeReferencesScanSerializer,
)
from projects.code_references.services import (
    get_code_references_for_feature_flag,
    record_scan,
)
from projects.code_references.types import (
    FeatureFlagCodeReferencesRepositorySummary,
    FeatureFlagCodeReferencesScan,
    VCSProvider,
)
from projects.models import Project

logger = structlog.get_logger("code_references")


class FeatureFlagCodeReferencesScanCreateAPIView(
    generics.CreateAPIView[FeatureFlagCodeReferencesScan],  # type: ignore[type-var]
):
    """
    API view to create code references for a project
    """

    serializer_class = FeatureFlagCodeReferencesScanSerializer
    permission_classes = [SubmitFeatureFlagCodeReferences]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> response.Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        project = get_object_or_404(
            Project.objects.select_related("organisation"),
            pk=self.kwargs["project_pk"],
        )

        scan = record_scan(
            project=project,
            repository_url=validated_data["repository_url"],
            vcs_provider=VCSProvider(validated_data["vcs_provider"]),
            revision=validated_data["revision"],
            code_references=validated_data["code_references"],
        )

        feature_names = {ref["feature_name"] for ref in scan.code_references}
        logger.info(
            "scan.created",
            organisation__id=scan.project.organisation_id,
            code_references__count=len(scan.code_references),
            feature__count=len(feature_names),
        )

        return response.Response(
            data=self.get_serializer(scan).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["mcp"],
    extensions={
        "x-gram": {
            "name": "get_feature_code_references",
            "description": "Retrieves code references and usage information for the feature flag.",
        },
    },
)
class FeatureFlagCodeReferenceDetailAPIView(
    generics.RetrieveAPIView[FeatureFlagCodeReferencesRepositorySummary],  # type: ignore[type-var]
):
    """
    API view to retrieve code references for a specific feature in a project
    """

    serializer_class = FeatureFlagCodeReferencesRepositorySummarySerializer
    permission_classes = [ViewFeatureFlagCodeReferences]

    def get(self, *args: Any, **kwargs: Any) -> response.Response:
        feature = get_object_or_404(
            Feature,
            pk=self.kwargs["feature_pk"],
            project_id=self.kwargs["project_pk"],
        )
        return response.Response(get_code_references_for_feature_flag(feature))
