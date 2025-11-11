from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from pytest_django import DjangoAssertNumQueries

from core.constants import STRING
from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.versioning_service import (
    get_current_live_environment_feature_version,
    get_environment_flags_list,
    get_environment_flags_queryset,
    get_updated_feature_states_for_version,
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


def test_get_updated_feature_states_for_version_returns_empty_list_when_no_changes(
    environment_v2_versioning: Environment,
    feature: Feature,
    staff_user: FFAdminUser,
) -> None:
    # Given
    # v1 exists from fixture, create v2 with no changes
    v2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # When
    updated_feature_states = get_updated_feature_states_for_version(v2)

    # Then
    assert updated_feature_states == []


def test_get_updated_feature_states_for_version_returns_feature_state_when_enabled_changes(
    environment_v2_versioning: Environment,
    feature: Feature,
    staff_user: FFAdminUser,
) -> None:
    # Given
    v1 = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )
    v1_fs = v1.feature_states.first()

    # Create v2 with changed enabled flag
    v2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    v2_fs = v2.feature_states.first()
    v2_fs.enabled = not v1_fs.enabled  # Change enabled
    v2_fs.save()

    # When
    updated_feature_states = get_updated_feature_states_for_version(v2)

    # Then
    assert len(updated_feature_states) == 1
    assert updated_feature_states[0].id == v2_fs.id
    assert updated_feature_states[0].enabled is not v1_fs.enabled


def test_get_updated_feature_states_for_version_returns_feature_state_when_value_changes(
    environment_v2_versioning: Environment,
    feature: Feature,
    staff_user: FFAdminUser,
) -> None:
    # Given
    # v1 exists from fixture, create v2 with changed value
    v2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    v2_fs = v2.feature_states.first()
    v2_fs.feature_state_value.type = STRING
    v2_fs.feature_state_value.string_value = "changed_value"  # Different
    v2_fs.feature_state_value.save()
    v2_fs.save()

    # When
    updated_feature_states = get_updated_feature_states_for_version(v2)

    # Then
    assert len(updated_feature_states) == 1
    assert updated_feature_states[0].id == v2_fs.id
    assert updated_feature_states[0].get_feature_state_value() == "changed_value"


def test_get_updated_feature_states_for_version_returns_new_segment_override(
    environment_v2_versioning: Environment,
    feature: Feature,
    staff_user: FFAdminUser,
    segment: Segment,
) -> None:
    # Given
    # v1 exists from fixture, create v2 with a new segment override
    v2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    feature_segment = FeatureSegment.objects.create(
        segment=segment,
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=v2,
    )
    segment_override = FeatureState.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment=feature_segment,
        environment_feature_version=v2,
        enabled=True,
    )

    # When
    updated_feature_states = get_updated_feature_states_for_version(v2)

    # Then
    # Should only return the new segment override
    assert len(updated_feature_states) == 1
    assert updated_feature_states[0].id == segment_override.id
    assert updated_feature_states[0].feature_segment == feature_segment


def test_get_updated_feature_states_for_version_detects_environment_value_change(
    environment_v2_versioning: Environment,
    feature: Feature,
    staff_user: FFAdminUser,
    segment: Segment,
) -> None:
    # Given
    # Create v1 with environment feature state value and segment override
    v1 = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )
    v1_default = v1.feature_states.filter(feature_segment__isnull=True).first()
    v1_default.feature_state_value.type = STRING
    v1_default.feature_state_value.string_value = "default_value_v1"
    v1_default.feature_state_value.save()

    feature_segment_v1 = FeatureSegment.objects.create(
        segment=segment,
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=v1,
    )
    v1_segment_override = FeatureState.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment=feature_segment_v1,
        environment_feature_version=v1,
        enabled=True,
    )
    v1_segment_override.feature_state_value.type = STRING
    v1_segment_override.feature_state_value.string_value = "segment_value"
    v1_segment_override.feature_state_value.save()
    v1.publish(published_by=staff_user)

    # Create v2 - environment feature state value changes but segment override stays same
    v2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    v2_default = v2.feature_states.filter(feature_segment__isnull=True).first()
    v2_default.feature_state_value.string_value = "default_value_v2"  # Changed!
    v2_default.feature_state_value.save()

    # Segment override value stays the same (no changes to segment override)

    # When
    updated_feature_states = get_updated_feature_states_for_version(v2)

    # Then
    # Should only return the environment feature state(not the segment override)
    assert len(updated_feature_states) == 1
    assert updated_feature_states[0].feature_segment is None
    assert updated_feature_states[0].get_feature_state_value() == "default_value_v2"


def test_get_updated_feature_states_for_version_detects_segment_override_changes(
    environment_v2_versioning: Environment,
    feature: Feature,
    staff_user: FFAdminUser,
    segment: Segment,
) -> None:
    # Given
    # Create v1 with a segment override
    v1 = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )
    feature_segment_v1 = FeatureSegment.objects.create(
        segment=segment,
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=v1,
    )
    v1_segment_override = FeatureState.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment=feature_segment_v1,
        environment_feature_version=v1,
        enabled=False,
    )
    v1_segment_override.feature_state_value.type = STRING
    v1_segment_override.feature_state_value.string_value = "segment_value_v1"
    v1_segment_override.feature_state_value.save()
    v1.publish(published_by=staff_user)

    # Create v2 - segment override value changes but environment default stays same
    v2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    # Find the cloned segment override and change its value
    v2_segment_override = v2.feature_states.filter(
        feature_segment__segment=segment
    ).first()
    v2_segment_override.feature_state_value.string_value = (
        "segment_value_v2"  # Changed!
    )
    v2_segment_override.feature_state_value.save()

    # When
    updated_feature_states = get_updated_feature_states_for_version(v2)

    # Then
    # Should only return the segment override (not the environment default)
    assert len(updated_feature_states) == 1
    assert updated_feature_states[0].feature_segment is not None
    assert updated_feature_states[0].feature_segment.segment == segment
    assert updated_feature_states[0].get_feature_state_value() == "segment_value_v2"


def test_get_updated_feature_states_for_version_detects_multivariate_segment_override_weight_changes(
    environment_v2_versioning: Environment,
    feature: Feature,
    staff_user: FFAdminUser,
    segment: Segment,
) -> None:
    # Given
    # Create multivariate options for the feature
    mv_option_1 = MultivariateFeatureOption.objects.create(
        feature=feature,
        default_percentage_allocation=50,
        type=STRING,
        string_value="option_1",
    )
    mv_option_2 = MultivariateFeatureOption.objects.create(
        feature=feature,
        default_percentage_allocation=50,
        type=STRING,
        string_value="option_2",
    )

    # Create v1 with a segment override that has multivariate values
    v1 = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )
    feature_segment_v1 = FeatureSegment.objects.create(
        segment=segment,
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=v1,
    )
    v1_segment_override = FeatureState.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment=feature_segment_v1,
        environment_feature_version=v1,
        enabled=True,
    )
    MultivariateFeatureStateValue.objects.create(
        feature_state=v1_segment_override,
        multivariate_feature_option=mv_option_1,
        percentage_allocation=60,
    )
    MultivariateFeatureStateValue.objects.create(
        feature_state=v1_segment_override,
        multivariate_feature_option=mv_option_2,
        percentage_allocation=40,
    )
    v1.publish(published_by=staff_user)

    # Create v2 - change the multivariate percentage allocations in segment override
    v2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    v2_segment_override = v2.feature_states.filter(
        feature_segment__segment=segment
    ).first()
    v2_mv_value_1 = v2_segment_override.multivariate_feature_state_values.get(
        multivariate_feature_option=mv_option_1
    )
    v2_mv_value_1.percentage_allocation = 30
    v2_mv_value_1.save()

    v2_mv_value_2 = v2_segment_override.multivariate_feature_state_values.get(
        multivariate_feature_option=mv_option_2
    )
    v2_mv_value_2.percentage_allocation = 70
    v2_mv_value_2.save()

    # When
    updated_feature_states = get_updated_feature_states_for_version(v2)

    # Then
    # Should detect the change because multivariate allocations changed
    assert len(updated_feature_states) == 1
    assert updated_feature_states[0].feature_segment is not None
    assert updated_feature_states[0].feature_segment.segment == segment


def test_get_updated_feature_states_for_version_detects_segment_override_multivariate_value_changes(
    environment_v2_versioning: Environment,
    feature: Feature,
    staff_user: FFAdminUser,
    segment: Segment,
) -> None:
    # Given
    # Create multivariate options for the feature
    mv_option_1 = MultivariateFeatureOption.objects.create(
        feature=feature,
        default_percentage_allocation=50,
        type=STRING,
        string_value="option_1",
    )
    mv_option_2 = MultivariateFeatureOption.objects.create(
        feature=feature,
        default_percentage_allocation=50,
        type=STRING,
        string_value="option_2",
    )

    # Create v1 with a segment override
    v1 = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )
    feature_segment_v1 = FeatureSegment.objects.create(
        segment=segment,
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=v1,
    )
    v1_segment_override = FeatureState.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        feature_segment=feature_segment_v1,
        environment_feature_version=v1,
        enabled=True,
    )
    v1_segment_override.feature_state_value.type = STRING
    v1_segment_override.feature_state_value.string_value = "control_value"
    v1_segment_override.feature_state_value.save()
    MultivariateFeatureStateValue.objects.create(
        feature_state=v1_segment_override,
        multivariate_feature_option=mv_option_1,
        percentage_allocation=50,
    )
    MultivariateFeatureStateValue.objects.create(
        feature_state=v1_segment_override,
        multivariate_feature_option=mv_option_2,
        percentage_allocation=50,
    )
    v1.publish(published_by=staff_user)

    # Create v2 - change the control value but keep multivariate allocations the same
    v2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    v2_segment_override = v2.feature_states.filter(
        feature_segment__segment=segment
    ).first()
    v2_segment_override.feature_state_value.string_value = "new_control_value"
    v2_segment_override.feature_state_value.save()

    # When
    updated_feature_states = get_updated_feature_states_for_version(v2)

    # Then
    # Should detect the change because control value changed
    assert len(updated_feature_states) == 1
    assert updated_feature_states[0].feature_segment is not None
    assert updated_feature_states[0].feature_segment.segment == segment
    assert updated_feature_states[0].get_feature_state_value() == "new_control_value"
