import pytest

from environments.models import Environment
from features.feature_segments.services import get_reordered_priorities
from features.models import Feature, FeatureSegment
from projects.models import Project
from segments.models import Segment


@pytest.mark.parametrize(
    "new_priorities",
    [
        {0: 0},
        {3: 0},
        {0: 3},
        {1: 2},
        {2: 1},
        {0: 3, 3: 0},
        {0: 1, 1: 0},
        {1: 3, 2: 0},
        {0: 2, 1: 0, 2: 1},
        {0: 3, 1: 2, 2: 1, 3: 0},
        {0: 0, 1: 1, 2: 2, 3: 3},
    ],
)
def test_get_reordered_priorities__requested_priorities__matches_update_priorities(
    environment: Environment,
    feature: Feature,
    project: Project,
    new_priorities: dict[int, int],
) -> None:
    # Given
    feature_segments = [
        FeatureSegment.objects.create(
            feature=feature,
            environment=environment,
            segment=Segment.objects.create(name=f"segment {index}", project=project),
        )
        for index in range(4)
    ]
    requested_priorities = {
        feature_segments[index].id: priority
        for index, priority in new_priorities.items()
    }

    # When
    priorities = get_reordered_priorities(feature_segments, requested_priorities)

    # Then
    FeatureSegment.update_priorities(list(requested_priorities.items()))
    assert priorities == dict(
        FeatureSegment.objects.filter(
            id__in=[feature_segment.id for feature_segment in feature_segments]
        ).values_list("id", "priority")
    )
