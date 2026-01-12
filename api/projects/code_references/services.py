from datetime import timedelta
from urllib.parse import urljoin

from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import BooleanField, F, Func, OuterRef, QuerySet, Subquery, Value
from django.db.models.functions import JSONObject
from django.utils import timezone

from features.models import Feature
from projects.code_references.constants import (
    FEATURE_FLAG_CODE_REFERENCES_RETENTION_DAYS,
)
from projects.code_references.models import FeatureFlagCodeReferencesScan
from projects.code_references.types import (
    CodeReference,
    FeatureFlagCodeReferencesRepositorySummary,
    VCSProvider,
)


def annotate_feature_queryset_with_code_references_summary(
    queryset: QuerySet[Feature],
    project_id: int,
) -> QuerySet[Feature]:
    """Extend feature objects with a `code_references_counts`

    NOTE: This adds compatibility with `CodeReferenceRepositoryCountSerializer`
    while preventing N+1 queries from the serializer.
    """
    history_delta = timedelta(days=FEATURE_FLAG_CODE_REFERENCES_RETENTION_DAYS)
    cutoff_date = timezone.now() - history_delta

    # Early exit: if no scans exist for this project, skip the expensive annotation
    has_scans = FeatureFlagCodeReferencesScan.objects.filter(
        project_id=project_id,
        created_at__gte=cutoff_date,
    ).exists()

    if not has_scans:
        return queryset
    last_feature_found_at = (
        FeatureFlagCodeReferencesScan.objects.annotate(
            feature_name=OuterRef("feature_name"),
            contains_feature_name=Func(
                F("code_references"),
                Value("$[*] ? (@.feature_name == $feature_name)"),
                JSONObject(feature_name=F("feature_name")),
                function="jsonb_path_exists",
                output_field=BooleanField(),
            ),
        )
        .filter(
            project=OuterRef("project_id"),
            created_at__gte=timezone.now() - history_delta,
            repository_url=OuterRef("repository_url"),
            contains_feature_name=True,
        )
        .values("created_at")
        .order_by("-created_at")[:1]
    )
    counts_by_repository = (
        FeatureFlagCodeReferencesScan.objects
        # Count code references from JSON matching the feature name
        .annotate(
            feature_name=OuterRef("name"),
            last_feature_found_at=Subquery(last_feature_found_at),
            count=Func(
                Func(
                    F("code_references"),
                    Value("$[*] ? (@.feature_name == $feature_name)"),
                    JSONObject(feature_name=F("feature_name")),
                    function="jsonb_path_query_array",
                ),
                function="jsonb_array_length",
            ),
        )
        # Only from the latest scans of each repository
        .filter(
            created_at__gte=timezone.now() - history_delta,
            project_id=OuterRef("project_id"),
        )
        .order_by("repository_url", "-created_at")
        .distinct("repository_url")
        .values(
            json=JSONObject(
                repository_url=F("repository_url"),
                count=F("count"),
                last_successful_repository_scanned_at=F("created_at"),
                last_feature_found_at=F("last_feature_found_at"),
            ),
        )
    )

    return queryset.annotate(
        code_references_counts=ArraySubquery(counts_by_repository),
    )


def get_code_references_for_feature_flag(
    feature: Feature,
) -> list[FeatureFlagCodeReferencesRepositorySummary]:
    """Obtain a summary of latest code references for a feature

    Only query from the latest scans of each repository_url. This is used to
    populate `FeatureFlagCodeReferencesSerializer`.
    """
    history_delta = timedelta(days=FEATURE_FLAG_CODE_REFERENCES_RETENTION_DAYS)
    last_feature_found_at = (
        FeatureFlagCodeReferencesScan.objects.filter(
            project=feature.project,
            created_at__gte=timezone.now() - history_delta,
            repository_url=OuterRef("repository_url"),
            code_references__contains=[{"feature_name": feature.name}],
        )
        .values("created_at")
        .order_by("-created_at")[:1]
    )

    last_scans_of_each_repository = (
        FeatureFlagCodeReferencesScan.objects.filter(project=feature.project)
        .annotate(last_feature_found_at=Subquery(last_feature_found_at))
        .order_by("repository_url", "-created_at")
        .distinct("repository_url")
    )

    return [
        FeatureFlagCodeReferencesRepositorySummary(
            repository_url=scan.repository_url,
            vcs_provider=VCSProvider(scan.vcs_provider),
            revision=scan.revision,
            last_successful_repository_scanned_at=scan.created_at,
            last_feature_found_at=scan.last_feature_found_at,
            code_references=[
                CodeReference(
                    feature_name=feature.name,
                    file_path=reference["file_path"],
                    line_number=reference["line_number"],
                    permalink=_get_permalink(
                        provider=VCSProvider(scan.vcs_provider),
                        repository_url=scan.repository_url,
                        revision=scan.revision,
                        file_path=reference["file_path"],
                        line_number=reference["line_number"],
                    ),
                )
                for reference in scan.code_references
                if reference["feature_name"] == feature.name
            ],
        )
        for scan in last_scans_of_each_repository
    ]


def _get_permalink(
    provider: VCSProvider,
    repository_url: str,
    revision: str,
    file_path: str,
    line_number: int,
) -> str:
    """Generate a permalink for the code reference."""
    match provider:
        case VCSProvider.GITHUB:
            return urljoin(
                f"{repository_url}/",
                f"blob/{revision}/{file_path}#L{line_number}",
            )
    raise NotImplementedError(  # pragma: no cover
        f"Permalink generation for {provider} is not implemented."
    )
