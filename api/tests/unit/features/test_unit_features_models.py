from datetime import timedelta

import pytest
from django.utils import timezone

from features.models import Feature, FeatureState

now = timezone.now()
yesterday = now - timedelta(days=1)
tomorrow = now + timedelta(days=1)


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
        environment_id=environment.id
    )

    # Then
    assert feature_states.count() == 1
    assert feature_states.first() == feature_state_v2


def test_project_hide_disabled_flags_have_no_effect_on_feature_state_get_environment_flags_queryset(
    environment, project
):
    # Given
    project.hide_disabled_flags = True
    project.save()
    # two flags - one disable on enabled
    Feature.objects.create(default_enabled=False, name="disable_flag", project=project)
    Feature.objects.create(default_enabled=True, name="enabled_flag", project=project)

    # When
    feature_states = FeatureState.get_environment_flags_queryset(
        environment_id=environment.id
    )
    # Then
    assert feature_states.count() == 2


def test_feature_states_get_environment_flags_queryset_filter_using_feature_name(
    environment, project
):
    # Given
    Feature.objects.create(default_enabled=False, name="disable_flag", project=project)
    Feature.objects.create(default_enabled=True, name="enabled_flag", project=project)

    # When
    feature_states = FeatureState.get_environment_flags_queryset(
        environment_id=environment.id, feature_name="disabled_flag"
    )

    # Then
    assert feature_states.count() == 1
    assert feature_states.first().feature.name == "enabled_flag"


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


@pytest.mark.parametrize(
    "version, live_from, expected_is_live",
    (
        (1, yesterday, True),
        (None, None, False),
        (None, yesterday, False),
        (None, tomorrow, False),
        (1, tomorrow, False),
    ),
)
def test_feature_state_is_live(version, live_from, expected_is_live):
    assert (
        FeatureState(version=version, live_from=live_from).is_live == expected_is_live
    )
