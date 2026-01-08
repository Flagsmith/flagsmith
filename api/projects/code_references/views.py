from typing import Any

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, response

from features.models import Feature
from projects.code_references.models import FeatureFlagCodeReferencesScan
from projects.code_references.permissions import (
    SubmitFeatureFlagCodeReferences,
    ViewFeatureFlagCodeReferences,
)
from projects.code_references.serializers import (
    FeatureFlagCodeReferencesRepositorySummarySerializer,
    FeatureFlagCodeReferencesScanSerializer,
)
from projects.code_references.services import get_code_references_for_feature_flag
from projects.code_references.types import (
    FeatureFlagCodeReferencesRepositorySummary,
)


class FeatureFlagCodeReferencesScanCreateAPIView(
    generics.CreateAPIView[FeatureFlagCodeReferencesScan]
):
    """
    API view to create code references for a project
    """

    serializer_class = FeatureFlagCodeReferencesScanSerializer
    permission_classes = [SubmitFeatureFlagCodeReferences]

    def perform_create(  # type: ignore[override]
        self, serializer: FeatureFlagCodeReferencesScanSerializer
    ) -> None:
        serializer.save(project_id=self.kwargs["project_pk"])


@extend_schema(
    tags=["mcp"],
    extensions={
        "x-mcp-name": "get_feature_code_references",
        "x-mcp-description": "Retrieves code references and usage information for the feature flag.",
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
