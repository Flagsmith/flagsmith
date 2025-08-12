from rest_framework import generics

from .models import VCSFeatureFlagCodeReferences
from .permissions import SubmitCodeReferences
from .serializers import VCSFeatureFlagCodeReferencesSerializer


class CodeReferenceCreateAPIView(generics.CreateAPIView[VCSFeatureFlagCodeReferences]):
    """
    API view to create code references for a project
    """

    serializer_class = VCSFeatureFlagCodeReferencesSerializer
    permission_classes = [SubmitCodeReferences]

    def perform_create(  # type: ignore[override]
        self, serializer: VCSFeatureFlagCodeReferencesSerializer
    ) -> None:
        """
        Save the code references with the project context
        """
        serializer.save(project_id=self.kwargs["project_pk"])
