from django.db.models import Q

from environments.models import Environment
from features.versioning.models import EnvironmentFeatureVersion

SEGMENT_OVERRIDE_LIMIT_EXCEEDED_MESSAGE = (
    "The environment has reached the maximum allowed segments overrides limit."
)


def exceeds_segment_override_limit(
    environment: Environment,
    segment_ids_to_create_overrides: list[int] = None,
    segment_ids_to_delete_overrides: list[int] = None,
    exclusive: bool = False,
) -> bool:
    q = Q()

    segment_ids_to_create_overrides = segment_ids_to_create_overrides or []
    segment_ids_to_delete_overrides = segment_ids_to_delete_overrides or []

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

    existing_overridden_segment_ids = set(
        environment.feature_segments.filter(q).values_list("segment_id", flat=True)
    )
    segment_override_count = len(existing_overridden_segment_ids)

    extra = len(segment_ids_to_create_overrides) - len(
        set(segment_ids_to_delete_overrides).intersection(
            existing_overridden_segment_ids
        )
    )

    if _check(
        segment_override_count + extra,
        environment.project.max_segment_overrides_allowed,
    ):
        return True

    return False
