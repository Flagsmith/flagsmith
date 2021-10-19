from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from organisations.models import Organisation
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment


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

    @mock.patch("features.models.trigger_feature_state_change_webhooks")
    def test_cannot_create_duplicate_feature_state_in_an_environment(
        self, mock_trigger_webhooks
    ):
        """
        Note that although the mock isn't used in this test, it throws an exception on it's thread so we mock it
        here anyway.
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

    @mock.patch("features.models.trigger_feature_state_change_webhooks")
    def test_save_calls_trigger_webhooks(self, mock_trigger_webhooks):
        # Given
        feature_state = FeatureState.objects.get(
            feature=self.feature, environment=self.environment
        )

        # When
        feature_state.save()

        # Then
        mock_trigger_webhooks.assert_called_with(feature_state)


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
        identity=identity
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
    mock_get_mv_feature_state_value.assert_called_once_with(identity)
