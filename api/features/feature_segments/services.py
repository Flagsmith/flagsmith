from django.db.models import Max

from environments.models import Environment
from features.models import Feature, FeatureSegment
from features.versioning.versioning_service import (
    get_current_live_environment_feature_version,
)


def get_next_segment_override_priority(
    *, environment: Environment, feature: Feature
) -> int:
    version = (
        get_current_live_environment_feature_version(environment.id, feature.id)
        if environment.use_v2_feature_versioning
        else None
    )
    highest_priority: int | None = FeatureSegment.objects.filter(
        environment=environment,
        feature=feature,
        environment_feature_version=version,
    ).aggregate(highest_priority=Max("priority"))["highest_priority"]
    return 0 if highest_priority is None else highest_priority + 1
