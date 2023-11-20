from datetime import timedelta
from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from environments.identities.models import Identity
from environments.models import Environment
from features.constants import ENVIRONMENT, FEATURE_SEGMENT, IDENTITY
from features.models import Feature, FeatureSegment, FeatureState
from features.workflows.core.models import ChangeRequest
from organisations.models import Organisation
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment

now = timezone.now()
yesterday = now - timedelta(days=1)
tomorrow = now + timedelta(days=1)


@pytest.mark.django_db
class FeatureTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Test Org")
        self.project = Project.objects.create(
            name="Test Project", organisation=self.organisation
        )
        self.environment_one = Environment.objects.create(
            name="Test Environment 1", project=self.project
        )
        self.environment_two = Environment.objects.create(
            name="Test Environment 2", project=self.project
        )

    def test_feature_should_create_feature_states_for_environments(self):
        feature = Feature.objects.create(name="Test Feature", project=self.project)

        feature_states = FeatureState.objects.filter(feature=feature)

        self.assertEquals(feature_states.count(), 2)

    def test_save_existing_feature_should_not_change_feature_state_enabled(self):
        # Given
        default_enabled = True
        feature = Feature.objects.create(
            name="Test Feature", project=self.project, default_enabled=default_enabled
        )

        # When
        # we update the default_enabled state of the feature and save it again
        feature.default_enabled = not default_enabled
        feature.save()

        # Then
        # we expect that the feature state enabled values have not changed
        assert all(fs.enabled == default_enabled for fs in feature.feature_states.all())

    def test_creating_feature_with_initial_value_should_set_value_for_all_feature_states(
        self,
    ):
        feature = Feature.objects.create(
            name="Test Feature",
            project=self.project,
            initial_value="This is a value",
        )

        feature_states = FeatureState.objects.filter(feature=feature)

        for feature_state in feature_states:
            self.assertEquals(
                feature_state.get_feature_state_value(), "This is a value"
            )

    def test_creating_feature_with_integer_initial_value_should_set_integer_value_for_all_feature_states(
        self,
    ):
        # Given
        initial_value = 1
        feature = Feature.objects.create(
            name="Test feature",
            project=self.project,
            initial_value=initial_value,
        )

        # When
        feature_states = FeatureState.objects.filter(feature=feature)

        # Then
        for feature_state in feature_states:
            assert feature_state.get_feature_state_value() == initial_value

    def test_creating_feature_with_boolean_initial_value_should_set_boolean_value_for_all_feature_states(
        self,
    ):
        # Given
        initial_value = False
        feature = Feature.objects.create(
            name="Test feature",
            project=self.project,
            initial_value=initial_value,
        )

        # When
        feature_states = FeatureState.objects.filter(feature=feature)

        # Then
        for feature_state in feature_states:
            assert feature_state.get_feature_state_value() == initial_value

    def test_updating_feature_state_should_trigger_webhook(self):
        Feature.objects.create(name="Test Feature", project=self.project)
        # TODO: implement webhook test method

    def test_cannot_create_feature_with_same_case_insensitive_name(self):
        # Given
        feature_name = "Test Feature"

        feature_one = Feature(project=self.project, name=feature_name)
        feature_two = Feature(project=self.project, name=feature_name.lower())

        # When
        feature_one.save()

        # Then
        with pytest.raises(IntegrityError):
            feature_two.save()

    def test_updating_feature_name_should_update_feature_states(self):
        # Given
        old_feature_name = "old_feature"
        new_feature_name = "new_feature"

        feature = Feature.objects.create(project=self.project, name=old_feature_name)

        # When
        feature.name = new_feature_name
        feature.save()

        # Then
        FeatureState.objects.filter(feature__name=new_feature_name).exists()

    def test_full_clean_fails_when_duplicate_case_insensitive_name(self):
        # unit test to validate validate_unique() method

        # Given
        feature_name = "Test Feature"
        Feature.objects.create(
            name=feature_name, initial_value="test", project=self.project
        )

        # When
        with self.assertRaises(ValidationError):
            feature_two = Feature(
                name=feature_name.lower(),
                initial_value="test",
                project=self.project,
            )
            feature_two.full_clean()

    def test_updating_feature_should_allow_case_insensitive_name(self):
        # Given
        feature_name = "Test Feature"

        feature = Feature.objects.create(
            project=self.project, name=feature_name, initial_value="test"
        )

        # When
        feature.name = feature_name.lower()
        feature.full_clean()  # should not raise error as the same Object

    def test_when_create_feature_with_tags_then_success(self):
        # Given
        tag1 = Tag.objects.create(
            label="Test Tag",
            color="#fffff",
            description="Test Tag description",
            project=self.project,
        )
        tag2 = Tag.objects.create(
            label="Test Tag",
            color="#fffff",
            description="Test Tag description",
            project=self.project,
        )
        feature = Feature.objects.create(project=self.project, name="test feature")

        # When
        tags_for_feature = Tag.objects.all()
        feature.tags.set(tags_for_feature)
        feature.save()

        self.assertEqual(feature.tags.count(), 2)
        self.assertEqual(list(feature.tags.all()), [tag1, tag2])


@pytest.mark.django_db
class FeatureStateTest(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test org")
        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            name="Test environment", project=self.project
        )
        self.feature = Feature.objects.create(name="Test feature", project=self.project)

    @mock.patch("features.signals.trigger_feature_state_change_webhooks")
    def test_cannot_create_duplicate_feature_state_in_an_environment(
        self, mock_trigger_webhooks
    ):
        """
        Note that although the mock isn't used in this test, it throws an exception on
        it's thread so we mock it here anyway.
        """

        # Given
        duplicate_feature_state = FeatureState(
            feature=self.feature, environment=self.environment, enabled=True
        )

        # When
        with pytest.raises(ValidationError):
            duplicate_feature_state.save()

        # Then
        assert (
            FeatureState.objects.filter(
                feature=self.feature, environment=self.environment
            ).count()
            == 1
        )

    @mock.patch("features.signals.trigger_feature_state_change_webhooks")
    def test_cannot_create_duplicate_feature_state_in_an_environment_for_segment(
        self, mock_trigger_webhooks
    ):
        """
        Note that although the mock isn't used in this test, it throws an exception on
        it's thread so we mock it here anyway.
        """

        # Given
        segment = Segment.objects.create(project=self.project)
        feature_segment = FeatureSegment.objects.create(
            feature=self.feature, environment=self.environment, segment=segment
        )
        FeatureState.objects.create(
            feature=self.feature,
            environment=self.environment,
            feature_segment=feature_segment,
        )

        duplicate_feature_state = FeatureState(
            feature=self.feature,
            environment=self.environment,
            enabled=True,
            feature_segment=feature_segment,
        )

        # When
        with pytest.raises(ValidationError):
            duplicate_feature_state.save()

        # Then
        assert (
            FeatureState.objects.filter(
                feature=self.feature,
                environment=self.environment,
                feature_segment=feature_segment,
            ).count()
            == 1
        )

    @mock.patch("features.signals.trigger_feature_state_change_webhooks")
    def test_cannot_create_duplicate_feature_state_in_an_environment_for_identity(
        self, mock_trigger_webhooks
    ):
        """
        Note that although the mock isn't used in this test, it throws an exception on
        it's thread so we mock it here anyway.
        """

        # Given
        identity = Identity.objects.create(
            identifier="identifier", environment=self.environment
        )
        FeatureState.objects.create(
            feature=self.feature, environment=self.environment, identity=identity
        )

        duplicate_feature_state = FeatureState(
            feature=self.feature,
            environment=self.environment,
            enabled=True,
            identity=identity,
        )

        # When
        with pytest.raises(ValidationError):
            duplicate_feature_state.save()

        # Then
        assert (
            FeatureState.objects.filter(
                feature=self.feature, environment=self.environment, identity=identity
            ).count()
            == 1
        )

    def test_feature_state_gt_operator(self):
        # Given
        identity = Identity.objects.create(
            identifier="test_identity", environment=self.environment
        )
        segment_1 = Segment.objects.create(name="Test Segment 1", project=self.project)
        segment_2 = Segment.objects.create(name="Test Segment 2", project=self.project)
        feature_segment_p1 = FeatureSegment.objects.create(
            segment=segment_1,
            feature=self.feature,
            environment=self.environment,
            priority=1,
        )
        feature_segment_p2 = FeatureSegment.objects.create(
            segment=segment_2,
            feature=self.feature,
            environment=self.environment,
            priority=2,
        )

        # When
        identity_state = FeatureState.objects.create(
            identity=identity, feature=self.feature, environment=self.environment
        )

        segment_1_state = FeatureState.objects.create(
            feature_segment=feature_segment_p1,
            feature=self.feature,
            environment=self.environment,
        )
        segment_2_state = FeatureState.objects.create(
            feature_segment=feature_segment_p2,
            feature=self.feature,
            environment=self.environment,
        )
        default_env_state = FeatureState.objects.get(
            environment=self.environment, identity=None, feature_segment=None
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
        self,
    ):
        # Given
        another_environment = Environment.objects.create(
            name="Another environment", project=self.project
        )
        feature_state_env_1 = FeatureState.objects.filter(
            environment=self.environment
        ).first()
        feature_state_env_2 = FeatureState.objects.filter(
            environment=another_environment
        ).first()

        # When
        with pytest.raises(ValueError):
            feature_state_env_1 > feature_state_env_2

        # Then - exception raised

    def test_feature_state_gt_operator_throws_value_error_if_different_features(self):
        # Given
        another_feature = Feature.objects.create(
            name="Another feature", project=self.project
        )
        feature_state_env_1 = FeatureState.objects.filter(feature=self.feature).first()
        feature_state_env_2 = FeatureState.objects.filter(
            feature=another_feature
        ).first()

        # When
        with pytest.raises(ValueError):
            feature_state_env_1 > feature_state_env_2

        # Then - exception raised

    def test_feature_state_gt_operator_throws_value_error_if_different_identities(self):
        # Given
        identity_1 = Identity.objects.create(
            identifier="identity_1", environment=self.environment
        )
        identity_2 = Identity.objects.create(
            identifier="identity_2", environment=self.environment
        )

        feature_state_identity_1 = FeatureState.objects.create(
            feature=self.feature, environment=self.environment, identity=identity_1
        )
        feature_state_identity_2 = FeatureState.objects.create(
            feature=self.feature, environment=self.environment, identity=identity_2
        )

        # When
        with pytest.raises(ValueError):
            feature_state_identity_1 > feature_state_identity_2

        # Then - exception raised

    @mock.patch("features.signals.trigger_feature_state_change_webhooks")
    def test_save_calls_trigger_webhooks(self, mock_trigger_webhooks):
        # Given
        feature_state = FeatureState.objects.get(
            feature=self.feature, environment=self.environment
        )

        # When
        feature_state.save()

        # Then
        mock_trigger_webhooks.assert_called_with(feature_state)

    def test_get_environment_flags_returns_latest_live_versions_of_feature_states(
        self,
    ):
        # Given
        feature_2 = Feature.objects.create(name="feature_2", project=self.project)
        feature_2_v1_feature_state = FeatureState.objects.get(feature=feature_2)

        feature_1_v2_feature_state = FeatureState.objects.create(
            feature=self.feature,
            enabled=True,
            version=2,
            environment=self.environment,
            live_from=timezone.now(),
        )
        FeatureState.objects.create(
            feature=self.feature,
            enabled=False,
            version=None,
            environment=self.environment,
        )

        identity = Identity.objects.create(
            identifier="identity", environment=self.environment
        )
        FeatureState.objects.create(
            feature=self.feature, identity=identity, environment=self.environment
        )

        # When
        environment_feature_states = FeatureState.get_environment_flags_list(
            environment_id=self.environment.id,
            additional_filters=Q(feature_segment=None, identity=None),
        )

        # Then
        assert set(environment_feature_states) == {
            feature_1_v2_feature_state,
            feature_2_v1_feature_state,
        }

    def test_feature_state_type_environment(self):
        # Given
        feature_state = FeatureState.objects.get(
            environment=self.environment,
            feature=self.feature,
            identity=None,
            feature_segment=None,
        )

        # Then
        assert feature_state.type == ENVIRONMENT

    def test_feature_state_type_identity(self):
        # Given
        identity = Identity.objects.create(
            identifier="identity", environment=self.environment
        )
        feature_state = FeatureState.objects.create(
            environment=self.environment,
            feature=self.feature,
            identity=identity,
            feature_segment=None,
        )

        # Then
        assert feature_state.type == IDENTITY

    def test_feature_state_type_feature_segment(self):
        # Given
        segment = Segment.objects.create(project=self.project)
        feature_segment = FeatureSegment.objects.create(
            feature=self.feature, segment=segment, environment=self.environment
        )
        feature_state = FeatureState.objects.create(
            environment=self.environment,
            feature=self.feature,
            identity=None,
            feature_segment=feature_segment,
        )

        # Then
        assert feature_state.type == FEATURE_SEGMENT

    def test_feature_state_type_unknown(self):
        # Note: this test is a case which should never, ever happen in real life
        # as it's not possible to create a feature state that has both an identity
        # and a feature segment via the API, however, it's useful to have the logic
        # defined in case it ever does happen

        # Given
        # a feature state with both identity and feature segment
        identity = Identity.objects.create(
            identifier="identity", environment=self.environment
        )
        segment = Segment.objects.create(project=self.project)
        feature_segment = FeatureSegment.objects.create(
            feature=self.feature, segment=segment, environment=self.environment
        )
        feature_state = FeatureState.objects.create(
            environment=self.environment,
            feature=self.feature,
            identity=identity,
            feature_segment=feature_segment,
        )

        # Then
        # we default to environment type
        with self.assertLogs("features") as caplog:
            assert feature_state.type == ENVIRONMENT

        # and an error is logged
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert (
            caplog.records[0].message
            == f"FeatureState {feature_state.id} does not have a valid type. "
            f"Defaulting to environment."
        )


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


def test_feature_state_get_audit_log_related_object_id_returns_nothing_if_uncommitted_change_request(
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
    related_object_id = feature_state.get_audit_log_related_object_id(
        mocker.MagicMock(id="history_instance")
    )  # history instance is irrelevant here

    # Then
    assert related_object_id is None


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
