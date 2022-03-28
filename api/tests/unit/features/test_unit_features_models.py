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
        environments=[environment]
    )

    # Then
    assert feature_states.count() == 1
    assert feature_states.first() == feature_state_v2
