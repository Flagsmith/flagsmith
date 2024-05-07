from datetime import timedelta
from unittest import mock

import freezegun
import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.utils import timezone
from pytest_mock import MockerFixture

from environments.identities.models import Identity
from environments.models import Environment
from features.constants import ENVIRONMENT, FEATURE_SEGMENT, IDENTITY
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.workflows.core.models import ChangeRequest
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment
from users.models import FFAdminUser

now = timezone.now()
yesterday = now - timedelta(days=1)
tomorrow = now + timedelta(days=1)


def test_feature_should_create_feature_states_for_environments(
    db: None,
    environment: Environment,
    project: Project,
) -> None:
    # Given
    Environment.objects.create(name="Test Environment 2", project=project)

    # When
    feature = Feature.objects.create(name="Test Feature", project=project)

    # Then
    feature_states = FeatureState.objects.filter(feature=feature)
    assert feature_states.count() == 2


def test_save_existing_feature_should_not_change_feature_state_enabled(
    db: None,
    project: Project,
) -> None:
    # Given
    default_enabled = True
    feature = Feature.objects.create(
        name="Test Feature", project=project, default_enabled=default_enabled
    )

    # When
    # we update the default_enabled state of the feature and save it again
    feature.default_enabled = not default_enabled
    feature.save()

    # Then
    # we expect that the feature state enabled values have not changed
    assert all(fs.enabled == default_enabled for fs in feature.feature_states.all())


def test_creating_feature_with_initial_value_should_set_value_for_all_feature_states(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    Environment.objects.create(name="Test Environment 2", project=project)

    # When
    value = "This is a value"
    feature = Feature.objects.create(
        name="Test Feature", project=project, initial_value=value
    )

    # Then
    feature_states = FeatureState.objects.filter(feature=feature)

    assert feature_states.count() == 2
    for feature_state in feature_states:
        feature_state.get_feature_state_value() == value


def test_creating_feature_with_integer_initial_value_should_set_integer_value_for_all_feature_states(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    Environment.objects.create(name="Test Environment 2", project=project)

    initial_value = 1
    feature = Feature.objects.create(
        name="Test feature",
        project=project,
        initial_value=initial_value,
    )

    # When
    feature_states = FeatureState.objects.filter(feature=feature)

    # Then
    assert feature_states.count() == 2
    for feature_state in feature_states:
        assert feature_state.get_feature_state_value() == initial_value


def test_creating_feature_with_boolean_initial_value_should_set_boolean_value_for_all_feature_states(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    Environment.objects.create(name="Test Environment 2", project=project)

    initial_value = False
    feature = Feature.objects.create(
        name="Test feature",
        project=project,
        initial_value=initial_value,
    )

    # When
    feature_states = FeatureState.objects.filter(feature=feature)

    # Then
    assert feature_states.count() == 2
    for feature_state in feature_states:
        assert feature_state.get_feature_state_value() == initial_value


def test_cannot_create_feature_with_same_case_insensitive_name(
    project: Project,
) -> None:
    # Given
    feature_name = "Test Feature"

    feature_one = Feature(project=project, name=feature_name)
    feature_two = Feature(project=project, name=feature_name.lower())

    # When
    feature_one.save()

    # Then
    with pytest.raises(IntegrityError):
        feature_two.save()


def test_updating_feature_name_should_update_feature_states(
    project: Project,
) -> None:
    # Given
    old_feature_name = "old_feature"
    new_feature_name = "new_feature"

    feature = Feature.objects.create(project=project, name=old_feature_name)

    # When
    feature.name = new_feature_name
    feature.save()

    # Then
    FeatureState.objects.filter(feature__name=new_feature_name).exists()


def test_full_clean_fails_when_duplicate_case_insensitive_name(
    project: Project,
) -> None:
    # unit test to validate validate_unique() method

    # Given
    feature_name = "Test Feature"
    Feature.objects.create(name=feature_name, initial_value="test", project=project)

    # When
    with pytest.raises(ValidationError):
        feature_two = Feature(
            name=feature_name.lower(),
            initial_value="test",
            project=project,
        )
        feature_two.full_clean()


def test_updating_feature_should_allow_case_insensitive_name(project: Project) -> None:
    # Given
    feature_name = "Test Feature"
    feature = Feature.objects.create(
        project=project, name=feature_name, initial_value="test"
    )

    # When
    feature.name = feature_name.lower()
    # Should not raise error as the same Object.
    feature.full_clean()


def test_when_create_feature_with_tags_then_success(project: Project) -> None:
    # Given
    tag1 = Tag.objects.create(
        label="Test Tag",
        color="#fffff",
        description="Test Tag description",
        project=project,
    )
    tag2 = Tag.objects.create(
        label="Test Tag",
        color="#fffff",
        description="Test Tag description",
        project=project,
    )
    feature = Feature.objects.create(project=project, name="test feature")

    # When
    tags_for_feature = Tag.objects.all()
    feature.tags.set(tags_for_feature)
    feature.save()

    assert feature.tags.count() == 2
    assert list(feature.tags.all()) == [tag1, tag2]


def test_cannot_create_duplicate_feature_state_in_an_environment(
    feature: Feature,
    environment: Environment,
) -> None:

    # Given
    duplicate_feature_state = FeatureState(
        feature=feature, environment=environment, enabled=True
    )

    # When
    with pytest.raises(ValidationError):
        duplicate_feature_state.save()

    # Then
    assert (
        FeatureState.objects.filter(feature=feature, environment=environment).count()
        == 1
    )


def test_cannot_create_duplicate_feature_state_in_an_environment_for_segment(
    project: Project,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    segment = Segment.objects.create(project=project)
    feature_segment = FeatureSegment.objects.create(
        feature=feature, environment=environment, segment=segment
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
    )

    duplicate_feature_state = FeatureState(
        feature=feature,
        environment=environment,
        enabled=True,
        feature_segment=feature_segment,
    )

    # When
    with pytest.raises(ValidationError):
        duplicate_feature_state.save()

    # Then
    assert (
        FeatureState.objects.filter(
            feature=feature,
            environment=environment,
            feature_segment=feature_segment,
        ).count()
        == 1
    )


def test_cannot_create_duplicate_feature_state_in_an_environment_for_identity(
    project: Project,
    feature: Feature,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity
    )

    duplicate_feature_state = FeatureState(
        feature=feature,
        environment=environment,
        enabled=True,
        identity=identity,
    )

    # When
    with pytest.raises(ValidationError):
        duplicate_feature_state.save()

    # Then
    assert (
        FeatureState.objects.filter(
            feature=feature, environment=environment, identity=identity
        ).count()
        == 1
    )


def test_feature_state_gt_operator_order(
    identity: Identity,
    feature: Feature,
    environment: Environment,
    project: Project,
) -> None:
    # Given
    segment_1 = Segment.objects.create(name="Test Segment 1", project=project)
    segment_2 = Segment.objects.create(name="Test Segment 2", project=project)
    feature_segment_p1 = FeatureSegment.objects.create(
        segment=segment_1,
        feature=feature,
        environment=environment,
        priority=1,
    )
    feature_segment_p2 = FeatureSegment.objects.create(
        segment=segment_2,
        feature=feature,
        environment=environment,
        priority=2,
    )

    # When
    identity_state = FeatureState.objects.create(
        identity=identity, feature=feature, environment=environment
    )

    segment_1_state = FeatureState.objects.create(
        feature_segment=feature_segment_p1,
        feature=feature,
        environment=environment,
    )
    segment_2_state = FeatureState.objects.create(
        feature_segment=feature_segment_p2,
        feature=feature,
        environment=environment,
    )
    default_env_state = FeatureState.objects.get(
        environment=environment, identity=None, feature_segment=None
    )

    # Then - identity state is higher priority than all
    assert identity_state > segment_1_state
    assert identity_state > segment_2_state
    assert identity_state > default_env_state

    # and feature state with feature segment with highest priority is greater than feature state with lower
    # priority feature segment and default environment state
    assert segment_1_state > segment_2_state
    assert segment_1_state > default_env_state

    # and feature state with any segment is greater than default environment state
    assert segment_2_state > default_env_state


def test_feature_state_gt_operator_throws_value_error_if_different_environments(
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    another_environment = Environment.objects.create(
        name="Another environment", project=project
    )
    feature_state_env_1 = FeatureState.objects.filter(environment=environment).first()
    feature_state_env_2 = FeatureState.objects.filter(
        environment=another_environment
    ).first()

    # When / Then - exception raised
    with pytest.raises(ValueError):
        feature_state_env_1 > feature_state_env_2


def test_feature_state_gt_operator_throws_value_error_if_different_features(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    another_feature = Feature.objects.create(name="Another feature", project=project)
    feature_state_env_1 = FeatureState.objects.filter(feature=feature).first()
    feature_state_env_2 = FeatureState.objects.filter(feature=another_feature).first()

    # When / Then - exception raised
    with pytest.raises(ValueError):
        feature_state_env_1 > feature_state_env_2


def test_feature_state_gt_operator_throws_value_error_if_different_identities(
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    identity_1 = Identity.objects.create(
        identifier="identity_1", environment=environment
    )
    identity_2 = Identity.objects.create(
        identifier="identity_2", environment=environment
    )

    feature_state_identity_1 = FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity_1
    )
    feature_state_identity_2 = FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity_2
    )

    # When / Then - exception raised
    with pytest.raises(ValueError):
        feature_state_identity_1 > feature_state_identity_2


@mock.patch("features.signals.trigger_feature_state_change_webhooks")
def test_feature_state_save_calls_trigger_webhooks(
    mock_trigger_webhooks: mock.MagicMock,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)

    # When
    feature_state.save()

    # Then
    mock_trigger_webhooks.assert_called_with(feature_state)


def test_feature_state_type_environment(
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=feature,
        identity=None,
        feature_segment=None,
    )

    # Then
    assert feature_state.type == ENVIRONMENT


def test_feature_state_type_identity(
    identity: Identity,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    feature_state = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        identity=identity,
        feature_segment=None,
    )

    # Then
    assert feature_state.type == IDENTITY


def test_feature_state_type_feature_segment(
    segment: Segment,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment
    )
    feature_state = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        identity=None,
        feature_segment=feature_segment,
    )

    # Then
    assert feature_state.type == FEATURE_SEGMENT


@pytest.mark.parametrize("hashed_percentage", (0.0, 0.3, 0.5, 0.8, 0.999999))
@mock.patch("features.models.get_hashed_percentage_for_object_ids")
def test_get_multivariate_value_returns_correct_value_when_we_pass_identity(
    mock_get_hashed_percentage,
    hashed_percentage,
    multivariate_feature,
    environment,
    identity,
):
    # Given
    mock_get_hashed_percentage.return_value = hashed_percentage
    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )

    # When
    multivariate_value = feature_state.get_multivariate_feature_state_value(
        identity_hash_key=identity.get_hash_key()
    )

    # Then
    # we get a multivariate value
    assert multivariate_value

    # and that value is not the control (since the fixture includes values that span
    # the entire 100%)
    assert multivariate_value.value != multivariate_value.initial_value


@mock.patch.object(FeatureState, "get_multivariate_feature_state_value")
def test_get_feature_state_value_for_multivariate_features(
    mock_get_mv_feature_state_value, environment, multivariate_feature, identity
):
    # Given
    value = "value"
    mock_mv_feature_state_value = mock.MagicMock(value=value)
    mock_get_mv_feature_state_value.return_value = mock_mv_feature_state_value

    environment.use_identity_composite_key_for_hashing = False
    environment.save()

    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )

    # When
    feature_state_value = feature_state.get_feature_state_value(identity=identity)

    # Then
    # the correct value is returned
    assert feature_state_value == value
    # and the correct call is made to get the multivariate feature state value
    mock_get_mv_feature_state_value.assert_called_once_with(str(identity.id))


@mock.patch.object(FeatureState, "get_multivariate_feature_state_value")
def test_get_feature_state_value_for_multivariate_features_mv_v2_evaluation(
    mock_get_mv_feature_state_value, environment, multivariate_feature, identity
):
    # Given
    value = "value"
    mock_mv_feature_state_value = mock.MagicMock(value=value)
    mock_get_mv_feature_state_value.return_value = mock_mv_feature_state_value

    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )

    # When
    feature_state_value = feature_state.get_feature_state_value(identity=identity)

    # Then
    # the correct value is returned
    assert feature_state_value == value
    # and the correct call is made to get the multivariate feature state value
    mock_get_mv_feature_state_value.assert_called_once_with(identity.composite_key)


@pytest.mark.parametrize(
    "feature_state_version_generator",
    (
        # test the default case, this should never be true
        (None, None, None, None, False),
        # for the following 6 cases, ensure that we test in both directions
        (2, now, None, None, True),
        (None, None, 2, now, False),
        (2, now, 3, now, False),
        (3, now, 2, now, True),
        (3, now, 2, yesterday, True),
        (3, yesterday, 2, now, False),
    ),
    indirect=True,
)
def test_feature_state_gt_operator(feature_state_version_generator):
    first, second, expected_result = feature_state_version_generator
    assert (first > second) is expected_result


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
def test_feature_state_is_live(version, live_from, expected_is_live, environment):
    assert (
        FeatureState(
            version=version, live_from=live_from, environment=environment
        ).is_live
        == expected_is_live
    )


def test_creating_a_feature_with_defaults_does_not_set_defaults_if_disabled(
    project, environment
):
    # Given
    project.prevent_flag_defaults = True
    project.save()

    default_state = True
    default_value = "default"

    feature = Feature(
        project=project,
        name="test_flag_defaults",
        initial_value=default_value,
        default_enabled=default_state,
    )

    # When
    feature.save()

    # Then
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    assert feature_state.enabled is False
    assert not feature_state.get_feature_state_value()


def test_feature_state_get_skip_create_audit_log_if_uncommitted_change_request(
    environment, feature, admin_user
):
    # Given
    change_request = ChangeRequest.objects.create(
        environment=environment, title="Test CR", user=admin_user
    )
    feature_state = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        change_request=change_request,
        version=None,
    )

    # Then
    assert feature_state.get_skip_create_audit_log() is True


def test_feature_state_get_skip_create_audit_log_if_environment_feature_version(
    environment_v2_versioning, feature
):
    # Given
    environment_feature_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )
    feature_state = FeatureState.objects.get(
        environment=environment_v2_versioning,
        feature=feature,
        environment_feature_version=environment_feature_version,
    )

    # Then
    assert feature_state.get_skip_create_audit_log() is True


@pytest.mark.parametrize(
    "feature_segment_id, identity_id, expected_function_name",
    (
        (1, None, "get_segment_override_created_audit_message"),
        (None, 1, "get_identity_override_created_audit_message"),
        (None, None, "get_environment_feature_state_created_audit_message"),
    ),
)
def test_feature_state_get_create_log_message_calls_correct_helper_function(
    mocker,
    feature_segment_id,
    identity_id,
    environment,
    feature,
    expected_function_name,
):
    # Given
    mock_audit_helpers = mocker.patch("features.models.audit_helpers")
    feature_state = FeatureState(
        feature_segment_id=feature_segment_id,
        identity_id=identity_id,
        environment=environment,
        feature=feature,
    )

    # When
    feature_state.get_create_log_message(
        mocker.MagicMock(id="history_instance")
    )  # history instance is irrelevant here

    # Then
    expected_function = getattr(mock_audit_helpers, expected_function_name)
    expected_function.assert_called_once_with(feature_state)


def test_feature_state_get_create_log_message_returns_null_if_environment_created_after_feature(
    feature, mocker
):
    # Given
    environment = Environment.objects.create(
        name="Test environment", project=feature.project
    )
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)

    # When
    log = feature_state.get_create_log_message(mocker.MagicMock())

    # Then
    assert log is None


def test_feature_state_get_create_log_message_returns_value_if_environment_created_after_feature_for_override(
    feature, mocker, identity
):
    # Given
    environment = Environment.objects.create(
        name="Test environment", project=feature.project
    )
    feature_state = FeatureState.objects.create(
        environment=environment, feature=feature, identity=identity
    )

    # When
    log = feature_state.get_create_log_message(mocker.MagicMock())

    # Then
    assert log is not None


def test_feature_state_get_create_log_message_returns_message_if_environment_created_before_feature(
    environment, mocker
):
    # Given
    feature = Feature.objects.create(name="test_feature", project=environment.project)
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)

    # When
    log = feature_state.get_create_log_message(mocker.MagicMock())

    # Then
    assert log is not None


def test_feature_segment_update_priorities_when_no_changes(
    project, environment, feature, feature_segment, admin_user, mocker
):
    # Given
    mocked_create_segment_priorities_changed_audit_log = mocker.patch(
        "features.models.create_segment_priorities_changed_audit_log"
    )

    another_segment = Segment.objects.create(project=project, name="Another segment")
    FeatureSegment.objects.create(
        feature=feature,
        segment=another_segment,
        environment=environment,
        priority=feature_segment.priority + 1,
    )

    existing_feature_segments = FeatureSegment.objects.filter(
        environment=environment, feature=feature
    )
    existing_id_priority_pairs = FeatureSegment.to_id_priority_tuple_pairs(
        existing_feature_segments
    )

    # When
    returned_feature_segments = FeatureSegment.update_priorities(
        new_feature_segment_id_priorities=existing_id_priority_pairs
    )

    # Then
    assert list(returned_feature_segments) == list(existing_feature_segments)

    mocked_create_segment_priorities_changed_audit_log.delay.assert_not_called()


def test_feature_segment_update_priorities_when_changes(
    project, environment, feature, feature_segment, admin_user, mocker
):
    # Given
    mocked_create_segment_priorities_changed_audit_log = mocker.patch(
        "features.models.create_segment_priorities_changed_audit_log"
    )
    mocked_historical_records = mocker.patch("features.models.HistoricalRecords")
    mocked_request = mocker.MagicMock()
    mocked_historical_records.thread.request = mocked_request

    another_segment = Segment.objects.create(project=project, name="Another segment")
    another_feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=another_segment,
        environment=environment,
        priority=feature_segment.priority + 1,
    )

    existing_id_priority_pairs = FeatureSegment.to_id_priority_tuple_pairs(
        feature.feature_segments.filter(environment=environment)
    )
    new_id_priority_pairs = [(feature_segment.id, 1), (another_feature_segment.id, 0)]

    # When
    with freezegun.freeze_time(now):
        returned_feature_segments = FeatureSegment.update_priorities(
            new_feature_segment_id_priorities=new_id_priority_pairs
        )

    # Then
    assert sorted(
        FeatureSegment.to_id_priority_tuple_pairs(returned_feature_segments),
        key=lambda t: t[1],
    ) == sorted(new_id_priority_pairs, key=lambda t: t[1])

    mocked_create_segment_priorities_changed_audit_log.delay.assert_called_once_with(
        kwargs={
            "previous_id_priority_pairs": existing_id_priority_pairs,
            "feature_segment_ids": [feature_segment.id, another_feature_segment.id],
            "user_id": mocked_request.user.id,
            "master_api_key_id": mocked_request.master_api_key.id,
            "changed_at": now.isoformat(),
        }
    )


def test_feature_state_gt_operator_for_multiple_versions_of_segment_overrides(
    feature, segment, feature_segment, environment
):
    # Given
    v1_segment_override = FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment
    )
    v2_segment_override = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        version=2,
    )

    # Then
    assert v2_segment_override > v1_segment_override


def test_feature_state_gt_operator_for_segment_overrides_and_environment_default(
    feature, segment, feature_segment, environment
):
    # Given
    segment_override = FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment
    )
    environment_default = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        feature_segment__isnull=True,
        identity__isnull=True,
    )

    # Then
    assert segment_override > environment_default


def test_feature_state_clone_for_segment_override_clones_feature_segment(
    feature: Feature,
    segment_featurestate: FeatureState,
    environment: Environment,
    environment_two: Environment,
) -> None:
    # When
    cloned_fs = segment_featurestate.clone(env=environment_two, as_draft=True)

    # Then
    assert cloned_fs.feature_segment != segment_featurestate.feature_segment

    assert (
        cloned_fs.feature_segment.segment
        == segment_featurestate.feature_segment.segment
    )
    assert (
        cloned_fs.feature_segment.priority
        == segment_featurestate.feature_segment.priority
    )


def test_feature_segment_clone(
    feature_segment: FeatureSegment,
    environment: Environment,
    environment_two: Environment,
) -> None:
    # When
    cloned_feature_segment = feature_segment.clone(environment=environment_two)

    # Then
    assert cloned_feature_segment.id != feature_segment.id

    assert cloned_feature_segment.priority == feature_segment.priority
    assert cloned_feature_segment.segment == feature_segment.segment
    assert cloned_feature_segment.feature == feature_segment.feature
    assert cloned_feature_segment.environment == environment_two


def test_create_feature_creates_feature_states_in_all_environments_and_environment_feature_version(
    project: "Project",
) -> None:
    # Given
    Environment.objects.create(
        project=project, name="Environment 1", use_v2_feature_versioning=True
    )
    Environment.objects.create(
        project=project, name="Environment 2", use_v2_feature_versioning=True
    )

    # When
    feature = Feature.objects.create(name="test_feature", project=project)

    # Then
    assert EnvironmentFeatureVersion.objects.filter(feature=feature).count() == 2
    assert feature.feature_states.count() == 2


def test_webhooks_are_called_when_feature_state_is_updated(
    mocker: MockerFixture, feature_state: FeatureState
) -> None:
    # Given
    mock_trigger_feature_state_change_webhooks = mocker.patch(
        "features.signals.trigger_feature_state_change_webhooks"
    )

    # When
    feature_state.enabled = not feature_state.enabled
    feature_state.save()

    # Then
    mock_trigger_feature_state_change_webhooks.assert_called_once_with(feature_state)


def test_webhooks_are_called_when_feature_state_is_created(
    mocker: MockerFixture,
    feature: Feature,
    environment: Environment,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    mock_trigger_feature_state_change_webhooks = mocker.patch(
        "features.signals.trigger_feature_state_change_webhooks"
    )

    # When
    feature_state = FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment
    )

    # Then
    mock_trigger_feature_state_change_webhooks.assert_called_once_with(feature_state)


def test_webhooks_are_not_called_for_feature_state_with_environment_feature_version(
    mocker: MockerFixture,
    feature: Feature,
    environment_v2_versioning: Environment,
    segment: Segment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    mock_trigger_feature_state_change_webhooks = mocker.patch(
        "features.signals.trigger_feature_state_change_webhooks"
    )

    # When
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    feature_segment = FeatureSegment.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        segment=segment,
        environment_feature_version=new_version,
    )
    FeatureState.objects.create(
        feature=feature,
        environment_feature_version=new_version,
        environment=environment_v2_versioning,
        feature_segment=feature_segment,
    )
    new_version.publish(admin_user)

    # Then
    mock_trigger_feature_state_change_webhooks.assert_not_called()
