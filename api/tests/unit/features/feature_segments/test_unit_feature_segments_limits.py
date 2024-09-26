from environments.models import Environment
from features.feature_segments.limits import exceeds_segment_override_limit
from features.models import Feature
from projects.models import Project
from segments.models import Segment


def test_segment_override_limit_does_not_exclude_invalid_overrides_being_deleted(
    feature: Feature,
    segment: Segment,
    another_segment: Segment,
    environment_v2_versioning: Environment,
    project: Project,
) -> None:
    # Given
    project.max_segment_overrides_allowed = 0
    project.save()

    # When
    result = exceeds_segment_override_limit(
        environment=environment_v2_versioning,
        segment_ids_to_create_overrides=[another_segment.id],
        segment_ids_to_delete_overrides=[segment.id],
    )

    # Then
    assert result is True
