from datetime import timedelta

from django.db.models.expressions import Case, Exists, OuterRef, Value, When
from django.db.models.fields import BooleanField
from django.db.models.functions import Cast
from django.db.models.query import QuerySet
from django.utils import timezone

from app_analytics.services import get_features_in_use
from environments.models import Environment
from features.feature_lifecycle.types import LifecycleStage
from features.models import Feature
from integrations.flagsmith.client import get_openfeature_client
from organisations.models import Organisation
from projects.code_references.services import get_feature_flags_in_latest_scan
from projects.tags.models import Tag, TagType


def is_feature_lifecycle_enabled(organisation: Organisation) -> bool:
    return get_openfeature_client().get_boolean_value(
        "feature_lifecycle",
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )


def annotate_feature_queryset_with_lifecycle_stage(
    queryset: QuerySet[Feature],
    environment: Environment,
) -> QuerySet[Feature]:
    """Annotate `queryset` with `lifecycle_stage: LifecycleStage`."""
    days_until_stale = environment.project.stale_flags_limit_days
    usage_window = timezone.now() - timedelta(days=days_until_stale)

    features_in_code = get_feature_flags_in_latest_scan(environment.project)
    features_in_use = get_features_in_use(environment, since=usage_window)

    return queryset.alias(
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
    ).annotate(
        lifecycle_stage=Case(
            When(
                has_code_references=False,
                has_permanent_tag=False,
                has_stale_tag=False,
                then=Value(LifecycleStage.NEW),
            ),
            When(
                has_code_references=True,
                has_permanent_tag=False,
                has_stale_tag=False,
                then=Value(LifecycleStage.LIVE),
            ),
            When(
                has_code_references=True,
                has_permanent_tag=False,
                has_stale_tag=True,
                then=Value(LifecycleStage.STALE),
            ),
            When(
                has_permanent_tag=True,
                then=Value(LifecycleStage.PERMANENT),
            ),
            When(
                has_code_references=False,
                has_permanent_tag=False,
                has_stale_tag=True,
                has_recent_usage=True,
                then=Value(LifecycleStage.NEEDS_MONITORING),
            ),
            When(
                has_code_references=False,
                has_permanent_tag=False,
                has_stale_tag=True,
                has_recent_usage=False,
                then=Value(LifecycleStage.TO_REMOVE),
            ),
        ),
    )
