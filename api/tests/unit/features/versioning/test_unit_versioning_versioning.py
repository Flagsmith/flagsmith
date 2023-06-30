from django.db.models import Q
from django.utils import timezone

from environments.identities.models import Identity
from features.models import Feature, FeatureState
from features.versioning.versioning import (
    get_environment_flags_list,
    get_environment_flags_queryset,
)


def test_get_environment_flags_queryset_returns_only_latest_versions(
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
    feature_states = get_environment_flags_queryset(environment=environment)

    # Then
    assert feature_states.count() == 1
    assert feature_states.first() == feature_state_v2


def test_project_hide_disabled_flags_have_no_effect_on_get_environment_flags_queryset(
    environment, project
):
    # Given
    project.hide_disabled_flags = True
    project.save()
    # two flags - one disable on enabled
    Feature.objects.create(default_enabled=False, name="disable_flag", project=project)
    Feature.objects.create(default_enabled=True, name="enabled_flag", project=project)

    # When
    feature_states = get_environment_flags_queryset(environment=environment)

    # Then
    assert feature_states.count() == 2


def test_get_environment_flags_queryset_filter_using_feature_name(environment, project):
    # Given
    flag_1_name = "flag_1"
    Feature.objects.create(default_enabled=True, name=flag_1_name, project=project)
    Feature.objects.create(default_enabled=True, name="flag_2", project=project)

    # When
    feature_states = get_environment_flags_queryset(
        environment=environment, feature_name=flag_1_name
    )

    # Then
    assert feature_states.count() == 1
    assert feature_states.first().feature.name == "flag_1"


def test_get_environment_flags_returns_latest_live_versions_of_feature_states(
    project, environment, feature
):
    # Given
    feature_2 = Feature.objects.create(name="feature_2", project=project)
    feature_2_v1_feature_state = FeatureState.objects.get(feature=feature_2)

    feature_1_v2_feature_state = FeatureState.objects.create(
        feature=feature,
        enabled=True,
        version=2,
        environment=environment,
        live_from=timezone.now(),
    )
    FeatureState.objects.create(
        feature=feature,
        enabled=False,
        version=3,
        environment=environment,
    )

    identity = Identity.objects.create(identifier="identity", environment=environment)
    FeatureState.objects.create(
        feature=feature, identity=identity, environment=environment
    )

    # When
    environment_feature_states = get_environment_flags_list(
        environment=environment,
        additional_filters=Q(feature_segment=None, identity=None),
    )

    # Then
    assert set(environment_feature_states) == {
        feature_1_v2_feature_state,
        feature_2_v1_feature_state,
    }
