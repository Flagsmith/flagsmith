from datetime import timedelta

import pytest
from django.utils import timezone

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.workflows.core.models import ChangeRequest
from segments.models import Segment

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
    flag_1_name = "flag_1"
    Feature.objects.create(default_enabled=True, name=flag_1_name, project=project)
    Feature.objects.create(default_enabled=True, name="flag_2", project=project)

    # When
    feature_states = FeatureState.get_environment_flags_queryset(
        environment_id=environment.id, feature_name=flag_1_name
    )

    # Then
    assert feature_states.count() == 1
    assert feature_states.first().feature.name == "flag_1"


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
def test_feature_state_is_live(version, live_from, expected_is_live):
    assert (
        FeatureState(version=version, live_from=live_from).is_live == expected_is_live
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


def test_feature_state_get_create_log_message_returns_nothing_if_uncommitted_change_request(
    environment, feature, admin_user, mocker
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

    # When
    message = feature_state.get_create_log_message(
        mocker.MagicMock(id="history_instance")
    )  # history instance is irrelevant here

    # Then
    assert message is None


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
        }
    )


def test_feature_get_overrides_data(
    feature,
    environment,
    identity,
    segment,
    feature_segment,
    identity_featurestate,
    segment_featurestate,
):
    # Given
    # we create some other features with overrides to ensure we're only getting data
    # for each individual feature
    feature_2 = Feature.objects.create(project=feature.project, name="feature_2")
    FeatureState.objects.create(
        feature=feature_2, environment=environment, identity=identity
    )

    feature_3 = Feature.objects.create(project=feature.project, name="feature_3")
    feature_segment_for_feature_3 = FeatureSegment.objects.create(
        feature=feature_3, segment=segment, environment=environment
    )
    FeatureState.objects.create(
        feature=feature_3,
        environment=environment,
        feature_segment=feature_segment_for_feature_3,
    )

    # and an override for another identity that has been deleted
    another_identity = Identity.objects.create(
        identifier="another-identity", environment=environment
    )
    fs_to_delete = FeatureState.objects.create(
        feature=feature, environment=environment, identity=another_identity
    )
    fs_to_delete.delete()

    # When
    overrides_data = Feature.get_overrides_data(environment.id)

    # Then
    assert overrides_data[feature.id].num_identity_overrides == 1
    assert overrides_data[feature.id].num_segment_overrides == 1

    assert overrides_data[feature_2.id].num_identity_overrides == 1
    assert overrides_data[feature_2.id].num_segment_overrides == 0

    assert overrides_data[feature_3.id].num_identity_overrides is None
    assert overrides_data[feature_3.id].num_segment_overrides == 1


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
