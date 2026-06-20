import hashlib
import json
from collections import defaultdict
from urllib.parse import urljoin

from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import F, Func, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce, JSONObject
from django.utils import timezone

from features.models import Feature
from projects.code_references.models import ScannedCodeReferences, VCSRepository
from projects.code_references.types import (
    CodeReference,
    FeatureFlagCodeReferencesRepositorySummary,
    FeatureFlagCodeReferencesScan,
    StoredCodeReference,
    SubmittedCodeReference,
    VCSProvider,
)
from projects.models import Project


def annotate_feature_queryset_with_code_references_summary(
    queryset: QuerySet[Feature],
) -> QuerySet[Feature]:
    """Annotate `queryset` with `code_references_counts: list[CodeReferencesRepositoryCount]`."""

    count_from_last_scan = (
        ScannedCodeReferences.objects.filter(
            feature_id=OuterRef("feature_id"),
            repository_id=OuterRef("repository_id"),
            created_at=F("repository__last_scanned_at"),
        )
        .order_by("-created_at")
        .annotate(
            count=Func(F("code_references"), function="jsonb_array_length"),
        )
        .values("count")[:1]
    )

    counts_by_repository = (
        ScannedCodeReferences.objects.filter(
            feature_id=OuterRef("pk"),
        )
        .order_by("repository__url", "-created_at")
        .distinct("repository__url")
        .annotate(
            summary=JSONObject(
                repository_url=F("repository__url"),
                last_successful_repository_scanned_at=F("repository__last_scanned_at"),
                last_feature_found_at=F("created_at"),
                count=Coalesce(Subquery(count_from_last_scan), 0),
            ),
        )
        .values("summary")
    )

    return queryset.annotate(
        code_references_counts=ArraySubquery(counts_by_repository),
    )


def get_code_references_for_feature_flag(
    feature: Feature,
) -> list[FeatureFlagCodeReferencesRepositorySummary]:
    """Return the latest known code references for `feature` per repository."""

    latest_scanned_code_references = (
        ScannedCodeReferences.objects.filter(
            feature=feature,
            created_at=F("repository__last_scanned_at"),
        )
        .order_by("repository__url")
        .select_related("repository")
    )

    return [
        FeatureFlagCodeReferencesRepositorySummary(
            repository_url=r.repository.url,
            vcs_provider=(provider := VCSProvider(r.repository.vcs_provider)),
            revision=r.revision,
            last_successful_repository_scanned_at=r.repository.last_scanned_at,  # type: ignore[arg-type]
            last_feature_found_at=r.created_at,
            code_references=[
                CodeReference(
                    feature_name=feature.name,
                    file_path=ref["file_path"],
                    line_number=ref["line_number"],
                    permalink=_get_permalink(
                        provider=provider,
                        repository_url=r.repository.url,
                        revision=r.revision,
                        file_path=ref["file_path"],
                        line_number=ref["line_number"],
                    ),
                )
                for ref in r.code_references
            ],
        )
        for r in latest_scanned_code_references
    ]


def get_feature_flags_in_latest_scan(project: Project) -> QuerySet[Feature]:
    """Obtain features found in the latest code references scan"""
    fresh_scans = ScannedCodeReferences.objects.filter(
        feature__project=project,
        created_at=F("repository__last_scanned_at"),
    )
    features_in_scan: QuerySet[Feature] = Feature.objects.filter(
        scanned_code_references__in=fresh_scans,
    )
    return features_in_scan


def record_scan(
    project: Project,
    repository_url: str,
    vcs_provider: VCSProvider,
    revision: str,
    code_references: list[SubmittedCodeReference],
) -> FeatureFlagCodeReferencesScan:
    """Persist a code references scan and return its summary."""
    scanned_at = timezone.now()
    repository, _ = VCSRepository.objects.update_or_create(
        project=project,
        url=repository_url,
        defaults={"vcs_provider": vcs_provider, "last_scanned_at": scanned_at},
    )

    references_by_feature: dict[str, list[StoredCodeReference]] = defaultdict(list)
    for submitted in code_references:
        new_reference: StoredCodeReference = {
            "file_path": submitted["file_path"],
            "line_number": submitted["line_number"],
        }
        references_by_feature[submitted["feature_name"]].append(new_reference)

    features_by_name = {
        feature.name: feature
        for feature in Feature.objects.filter(
            project=project,
            name__in=references_by_feature,
        )
    }

    ScannedCodeReferences.objects.bulk_create(
        [
            ScannedCodeReferences(
                feature=feature,
                repository=repository,
                revision=revision,
                code_references=references,
                code_references_hash=_hash_references(references),
                created_at=scanned_at,
            )
            for feature_name, references in references_by_feature.items()
            if (feature := features_by_name.get(feature_name)) is not None
        ],
        update_conflicts=True,
        unique_fields=["feature", "repository", "code_references_hash"],
        update_fields=["created_at", "revision"],
    )

    return FeatureFlagCodeReferencesScan(
        created_at=scanned_at,
        repository_url=repository_url,
        vcs_provider=vcs_provider,
        revision=revision,
        code_references=code_references,
        project=project,
    )


def _hash_references(references: list[StoredCodeReference]) -> str:
    return hashlib.md5(
        json.dumps(references, sort_keys=True).encode(),
        usedforsecurity=False,
    ).hexdigest()


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
