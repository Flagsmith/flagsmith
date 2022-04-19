import pytest
from django.utils import timezone

from features.models import FeatureState


def test_feature_state_get_environment_flags_queryset_returns_only_latest_versions(
    feature, environment
):
    # Given
    feature_state_v1 = FeatureState.objects.get(
        feature=feature, environment=environment, feature_segment=None, identity=None
    )

    feature_state_v2 = feature_state_v1.clone(
        env=environment, live_from=timezone.now(), version=2
    )
    feature_state_v1.clone(env=environment, as_draft=True)  # draft feature state

    # When
    feature_states = FeatureState.get_environment_flags_queryset(
        environment=environment
    )

    # Then
    assert feature_states.count() == 1
    assert feature_states.first() == feature_state_v2


@pytest.mark.parametrize(
    "feature_state_version_generator",
    (
        (None, None, False),
        (2, None, True),
        (None, 2, False),
        (2, 3, False),
        (3, 2, True),
    ),
    indirect=True,
)
def test_feature_state_gt_operator_for_versions(feature_state_version_generator):
    first, second, expected_result = feature_state_version_generator
    assert (first > second) == expected_result
