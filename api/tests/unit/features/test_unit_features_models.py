from datetime import timedelta

import pytest
from django.utils import timezone

from environments.models import Environment
from features.models import Feature, FeatureState
from features.workflows.core.models import ChangeRequest

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
