from rest_framework import generics

from projects.code_references.models import FeatureFlagCodeReferencesScan
from projects.code_references.permissions import SubmitFeatureFlagCodeReferences
from projects.code_references.serializers import FeatureFlagCodeReferencesScanSerializer


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
