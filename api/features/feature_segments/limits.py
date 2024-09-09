from django.db.models import Q

from environments.models import Environment
from features.versioning.models import EnvironmentFeatureVersion

SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE = (
    "The environment has reached the maximum allowed segments overrides limit."
)


def exceeds_segment_override_limit(
    environment: Environment,
    extra: int = 0,
    exclusive: bool = False,
) -> bool:
    q = Q()

    def _check(left: int, right: int) -> bool:
        if exclusive:
            return left > right
        return left >= right

    if environment.use_v2_feature_versioning:
        latest_versions = (
            EnvironmentFeatureVersion.objects.get_latest_versions_by_environment_id(
                environment_id=environment.id
            )
        )
        q = q & Q(environment_feature_version__in=latest_versions)

    segment_override_count = environment.feature_segments.filter(q).count()
    if _check(
        segment_override_count + extra,
        environment.project.max_segment_overrides_allowed,
    ):
        return True

    return False
