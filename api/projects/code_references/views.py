from datetime import datetime
from functools import cache
from urllib.parse import urljoin

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import generics

from features.models import Feature
from projects.code_references.models import FeatureFlagCodeReferencesScan
from projects.code_references.permissions import (
    SubmitFeatureFlagCodeReferences,
    ViewFeatureFlagCodeReferences,
)
from projects.code_references.serializers import (
    FeatureFlagCodeReferencesScanSerializer,
    FeatureFlagCodeReferencesSerializer,
)
from projects.code_references.types import (
    CodeReference,
    FeatureFlagCodeReferences,
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


class FeatureFlagCodeReferenceDetailAPIView(
    generics.RetrieveAPIView[FeatureFlagCodeReferences],  # type: ignore[type-var]
):
    """
    API view to retrieve code references for a specific feature in a project
    """

    serializer_class = FeatureFlagCodeReferencesSerializer
    permission_classes = [ViewFeatureFlagCodeReferences]

    def get_object(self) -> FeatureFlagCodeReferences:
        return FeatureFlagCodeReferences(
            first_scanned_at=self._get_first_scanned_at(),
            last_scanned_at=self._get_last_scanned_at(),
            code_references=self._get_code_references(),
        )

    @cache
    def _get_feature(self) -> Feature:
        return get_object_or_404(
            Feature,
            project_id=self.kwargs["project_pk"],
            pk=self.kwargs["feature_pk"],
        )

    def _get_related_references(self) -> QuerySet[FeatureFlagCodeReferencesScan]:
        feature = self._get_feature()
        return FeatureFlagCodeReferencesScan.objects.filter(
            project_id=self.kwargs["project_pk"],
            code_references__contains=[{"feature_name": feature.name}],
        )

    def _get_first_scanned_at(self) -> datetime | None:
        related = self._get_related_references()
        first_match = related.only("created_at").order_by("created_at").first()
        return first_match.created_at if first_match else None

    def _get_last_scanned_at(self) -> datetime | None:
        related = self._get_related_references()
        last_match = related.only("created_at").order_by("-created_at").first()
        return last_match.created_at if last_match else None

    def _get_code_references(self) -> list[CodeReference]:
        feature = self._get_feature()
        last_scans_of_each_repository = (
            FeatureFlagCodeReferencesScan.objects.filter(
                project_id=self.kwargs["project_pk"],
            )
            .order_by("repository_url", "-created_at")
            .distinct("repository_url")
        )

        return [
            CodeReference(
                feature_name=feature.name,
                file_path=reference["file_path"],
                line_number=reference["line_number"],
                permalink=self._get_permalink(
                    repository_url=scan.repository_url,
                    revision=scan.revision,
                    file_path=reference["file_path"],
                    line_number=reference["line_number"],
                ),
                scanned_at=scan.created_at,
                revision=scan.revision,
            )
            for scan in last_scans_of_each_repository
            for reference in scan.code_references
            if reference["feature_name"] == feature.name
        ]

    def _get_permalink(
        self,
        repository_url: str,
        revision: str,
        file_path: str,
        line_number: int,
    ) -> str:
        """Generate a permalink for the code reference.

        NOTE: Only GitHub is supported right now.
        """
        return urljoin(repository_url, f"blob/{revision}/{file_path}#L{line_number}")
