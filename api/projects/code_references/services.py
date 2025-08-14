from datetime import timedelta

from django.contrib.postgres.expressions import ArraySubquery
from django.db.models import F, Func, OuterRef, QuerySet, Value
from django.db.models.functions import JSONObject
from django.utils import timezone

from features.models import Feature
from projects.code_references.models import FeatureFlagCodeReferencesScan


def annotate_feature_queryset_with_code_references_summary(
    queryset: QuerySet[Feature],
) -> QuerySet[Feature]:
    """Extend feature objects with a `code_references_counts`

    NOTE: This adds compatibility with `CodeReferenceRepositoryCountSerializer`
    while preventing N+1 queries from the serializer.
    """
    counts_by_repository = (
        FeatureFlagCodeReferencesScan.objects
        # Count code references from JSON matching the feature name
        .annotate(
            feature_name=OuterRef("name"),
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
        # Only from the latest scans of each repository, within a 30-day sanity window
        .filter(
            created_at__gte=timezone.now() - timedelta(days=30),
            project_id=OuterRef("project_id"),
        )
        .order_by("repository_url", "-created_at")
        .distinct("repository_url")
        .values(
            json=JSONObject(
                repository_url=F("repository_url"),
                count=F("count"),
            ),
        )
    )

    return queryset.annotate(
        code_references_counts=ArraySubquery(counts_by_repository),
    )
