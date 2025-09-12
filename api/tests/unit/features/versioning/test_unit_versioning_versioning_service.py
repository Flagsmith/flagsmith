from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from pytest_django import DjangoAssertNumQueries

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.versioning_service import (
    get_current_live_environment_feature_version,
    get_environment_flags_list,
    get_environment_flags_queryset,
)
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser


def test_get_environment_flags_queryset_returns_only_latest_versions(  # type: ignore[no-untyped-def]
    feature: Feature,
    environment: Environment,
    django_assert_num_queries: DjangoAssertNumQueries,
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
    with django_assert_num_queries(2):
        feature_states = get_environment_flags_queryset(environment=environment)

        # trigger the queryset to execute and ensure the number of queries is correct
        list(feature_states)

    # Then
    assert feature_states.count() == 1
    assert feature_states.first() == feature_state_v2


def test_project_hide_disabled_flags_have_no_effect_on_get_environment_flags_queryset(  # type: ignore[no-untyped-def]
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


def test_get_environment_flags_queryset_filter_using_feature_name(environment, project):  # type: ignore[no-untyped-def]  # noqa: E501
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
    assert feature_states.first().feature.name == "flag_1"  # type: ignore[union-attr]


def test_get_environment_flags_returns_latest_live_versions_of_feature_states(  # type: ignore[no-untyped-def]
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
        version=None,
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


def test_get_environment_flags_v2_versioning_returns_latest_live_versions_of_feature_states(
    project: Project,
    environment_v2_versioning: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    # a second feature with its corresponding environment feature version
    feature_2 = Feature.objects.create(name="feature_2", project=project)
    environment_feature_2_version_1 = EnvironmentFeatureVersion.objects.get(
        feature=feature_2, environment=environment_v2_versioning
    )
    environment_feature_2_version_1_feature_state = (
        environment_feature_2_version_1.feature_states.first()
    )

    # and a second version for the original feature, which will have had an
    # initial version already created for it
    environment_feature_1_version_2 = EnvironmentFeatureVersion.objects.create(
        feature=feature, environment=environment_v2_versioning
    )
    environment_feature_1_version_2_feature_state = (
        environment_feature_1_version_2.feature_states.first()
    )
    environment_feature_1_version_2_feature_state.enabled = True
    environment_feature_1_version_2_feature_state.save()
    environment_feature_1_version_2.publish(admin_user)

    # When
    with django_assert_num_queries(2):
        environment_feature_states = get_environment_flags_list(
            environment=environment_v2_versioning,
            additional_filters=Q(feature_segment=None, identity=None),
        )

    # Then
    assert set(environment_feature_states) == {
        environment_feature_1_version_2_feature_state,
        environment_feature_2_version_1_feature_state,
    }


def test_get_environment_flags_v2_versioning_does_not_return_removed_segment_override(
    project: Project,
    feature: Feature,
    admin_user: FFAdminUser,
    segment: Segment,
    segment_featurestate: FeatureState,
    environment_v2_versioning: Environment,
) -> None:
    # Given
    # The initial version has a segment override
    initial_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )
    assert FeatureState.objects.filter(
        feature=feature,
        environment=environment_v2_versioning,
        feature_segment__segment=segment,
        environment_feature_version=initial_version,
    ).exists()

    # Now let's create a new version, remove the segment override and publish the version
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    FeatureState.objects.filter(
        feature=feature,
        environment=environment_v2_versioning,
        feature_segment__segment=segment,
        environment_feature_version=new_version,
    ).delete()
    new_version.publish(published_by=admin_user)

    # When
    environment_feature_states = get_environment_flags_list(
        environment=environment_v2_versioning,
    )

    # Then
    assert len(environment_feature_states) == 1


def test_get_current_live_environment_feature_version(
    environment_v2_versioning: Environment, staff_user: FFAdminUser, feature: Feature
) -> None:
    # Given
    # The initial version
    version_1 = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )

    # and an unpublished version
    EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # and a version that is published but not yet live
    future_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    future_version.publish(staff_user, live_from=timezone.now() + timedelta(days=1))

    # When
    latest_version = get_current_live_environment_feature_version(
        environment_id=environment_v2_versioning.id, feature_id=feature.id
    )

    # Then
    assert latest_version == version_1
