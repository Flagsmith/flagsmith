import pytest
from django.test import TestCase, TransactionTestCase

from environments.models import Environment, Identity, Trait
from features.models import Feature, FeatureState, FeatureSegment, CONFIG
from features.utils import INTEGER, STRING, BOOLEAN
from organisations.models import Organisation
from projects.models import Project
from segments.models import Segment, SegmentRule, Condition, EQUAL, GREATER_THAN_INCLUSIVE, GREATER_THAN
from util.tests import Helper


@pytest.mark.django_db
class EnvironmentSaveTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Test Org")
        self.project = Project.objects.create(name="Test Project", organisation=self.organisation)
        self.feature = Feature.objects.create(name="Test Feature", project=self.project)
        # The environment is initialised in a non-saved state as we want to test the save
        # functionality.
        self.environment = Environment(name="Test Environment", project=self.project)

    def test_environment_should_be_created_with_feature_states(self):
        # Given - set up data

        # When
        self.environment.save()

        # Then
        feature_states = FeatureState.objects.filter(environment=self.environment)
        assert hasattr(self.environment, 'api_key')
        assert feature_states.count() == 1

    def test_on_creation_save_feature_states_get_created(self):
        # These should be no feature states before saving
        self.assertEqual(FeatureState.objects.count(), 0)

        self.environment.save()

        # On the first save a new feature state should be created
        self.assertEqual(FeatureState.objects.count(), 1)

    def test_on_update_save_feature_states_get_updated_not_created(self):
        self.environment.save()

        self.feature.default_enabled = True
        self.feature.save()
        self.environment.save()

        self.assertEqual(FeatureState.objects.count(), 1)

    def test_on_creation_save_feature_is_created_with_the_correct_default(self):
        self.environment.save()
        self.assertFalse(FeatureState.objects.get().enabled)

    def test_on_update_save_feature_gets_updated_with_the_correct_default(self):
        self.environment.save()
        self.assertFalse(FeatureState.objects.get().enabled)

        self.feature.default_enabled = True
        self.feature.save()

        self.assertTrue(FeatureState.objects.get().enabled)

    def test_on_update_save_feature_states_dont_get_updated_if_identity_present(self):
        self.environment.save()
        identity = Identity.objects.create(identifier="test-identity", environment=self.environment)

        fs = FeatureState.objects.get()
        fs.id = None
        fs.identity = identity
        fs.save()
        self.assertEqual(FeatureState.objects.count(), 2)

        self.feature.default_enabled = True
        self.feature.save()
        self.environment.save()
        fs.refresh_from_db()

        self.assertNotEqual(fs.enabled, FeatureState.objects.exclude(id=fs.id).get().enabled)


class IdentityTestCase(TransactionTestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Test Org")
        self.project = Project.objects.create(name="Test Project", organisation=self.organisation)
        self.project_flag_disabled = Project.objects.create(name="Project Flag Disabled",
                                                          organisation=self.organisation,
                                                          hide_disabled_flags=True)
        self.environment = Environment.objects.create(name="Test Environment", project=self.project)

    def tearDown(self) -> None:
        Helper.clean_up()

    def test_create_identity_should_assign_relevant_attributes(self):
        identity = Identity.objects.create(identifier="test-identity", environment=self.environment)

        assert isinstance(identity.environment, Environment)
        assert hasattr(identity, 'created_date')

    def test_get_all_feature_states(self):
        feature = Feature.objects.create(name="Test Feature", project=self.project)
        feature_2 = Feature.objects.create(name="Test Feature 2", project=self.project)
        environment_2 = Environment.objects.create(name="Test Environment 2", project=self.project)

        identity_1 = Identity.objects.create(
            identifier="test-identity-1",
            environment=self.environment,
        )
        identity_2 = Identity.objects.create(
            identifier="test-identity-2",
            environment=self.environment,
        )
        identity_3 = Identity.objects.create(
            identifier="test-identity-3",
            environment=environment_2,
        )

        # User unassigned - automatically should be created via `Feature` save method.
        fs_environment_anticipated = FeatureState.objects.get(
            feature=feature_2,
            environment=self.environment,
        )

        # User assigned
        fs_identity_anticipated = FeatureState.objects.create(
            feature=feature,
            environment=self.environment,
            identity=identity_1,
        )
        FeatureState.objects.create(
            feature=feature,
            environment=self.environment,
            identity=identity_2,
        )
        FeatureState.objects.create(
            feature=feature,
            environment=environment_2,
            identity=identity_3,
        )

        # For identity_1 all items in a different environment should not appear. Identity
        # specific flags should be returned as well as non-identity specific ones that have not
        # already been returned via the identity specific result.
        flags = identity_1.get_all_feature_states()
        self.assertEqual(len(flags), 2)
        self.assertIn(fs_environment_anticipated, flags)
        self.assertIn(fs_identity_anticipated, flags)

    def test_get_all_feature_states_exclude_disabled(self):

        feature = Feature.objects.create(name="Test Feature", project=self.project_flag_disabled)
        feature_2 = Feature.objects.create(name="Test Feature 2", project=self.project_flag_disabled)
        feature_3 = Feature.objects.create(name="Test Feature 3", project=self.project_flag_disabled, type=CONFIG)
        other_environment = Environment.objects.create(name="Test Environment 2", project=self.project_flag_disabled)

        identity_1 = Identity.objects.create(
            identifier="test-identity-1",
            environment=other_environment,
        )
        identity_2 = Identity.objects.create(
            identifier="test-identity-2",
            environment=self.environment,
        )

        # User assigned
        FeatureState.objects.create(
            feature=feature,
            environment=other_environment,
            enabled=True,
            identity=identity_1,
        )
        fs_identity_ignored = FeatureState.objects.create(
            feature=feature_2,
            environment=other_environment,
            enabled=False,
            identity=identity_1,
        )
        fs_identity_anticipated = FeatureState.objects.create(
            feature=feature_3,
            environment=other_environment,
            enabled=False,
            identity=identity_1,
        )
        FeatureState.objects.create(
            feature=feature,
            environment=self.environment,
            identity=identity_2,
        )

        # Disabled Feature of type FLAG should be ignored if
        # Project has hide_disabled_flags = True.
        flags = identity_1.get_all_feature_states()
        self.assertEqual(len(flags), 2)
        self.assertNotIn(fs_identity_ignored, flags)
        self.assertIn(fs_identity_anticipated, flags)

    def test_create_trait_should_assign_relevant_attributes(self):
        identity = Identity.objects.create(identifier='test-identity', environment=self.environment)
        trait = Trait.objects.create(trait_key="test-key", string_value="testing trait", identity=identity)

        self.assertIsInstance(trait.identity, Identity)
        self.assertTrue(hasattr(trait, 'trait_key'))
        self.assertTrue(hasattr(trait, 'value_type'))
        self.assertTrue(hasattr(trait, 'created_date'))

    def test_on_update_trait_should_update_relevant_attributes(self):
        identity = Identity.objects.create(identifier='test-identifier', environment=self.environment)
        trait = Trait.objects.create(trait_key="test-key", string_value="testing trait", identity=identity)

        # TODO: need tests for updates

    def test_get_all_traits_for_identity(self):
        identity = Identity.objects.create(identifier='test-identifier', environment=self.environment)
        identity2 = Identity.objects.create(identifier="test-identity_two", environment=self.environment)

        Trait.objects.create(trait_key="test-key-one", string_value="testing trait", identity=identity)
        Trait.objects.create(trait_key="test-key-two", string_value="testing trait", identity=identity)
        Trait.objects.create(trait_key="test-key-three", string_value="testing trait", identity=identity)
        Trait.objects.create(trait_key="test-key-three", string_value="testing trait", identity=identity2)

        # Identity one should have 3
        traits_identity_one = identity.get_all_user_traits()
        self.assertEqual(len(traits_identity_one), 3)

        traits_identity_two = identity2.get_all_user_traits()
        self.assertEqual(len(traits_identity_two), 1)

    def test_get_all_feature_states_for_identity_returns_correct_values_for_matching_segment(self):
        # Given
        trait_key = 'trait-key'
        trait_value = 'trait-value'
        identity = Identity.objects.create(identifier='test-identity', environment=self.environment)
        Trait.objects.create(identity=identity, trait_key=trait_key, string_value=trait_value)

        segment = Segment.objects.create(name='Test segment', project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(rule=rule, property=trait_key, value=trait_value, operator=EQUAL)

        feature_flag = Feature.objects.create(name='test-feature-flag', project=self.project, type='FLAG')
        remote_config = Feature.objects.create(name='test-remote-config', project=self.project,
                                               initial_value='initial-value', type='CONFIG')

        FeatureSegment.objects.create(feature=feature_flag, segment=segment, environment=self.environment, enabled=True)
        overridden_value = 'overridden-value'
        FeatureSegment.objects.create(feature=remote_config, segment=segment, environment=self.environment,
                                      value=overridden_value, value_type=STRING)

        # When
        feature_states = identity.get_all_feature_states()

        # Then
        feature_flag_state = next(filter(lambda fs: fs.feature == feature_flag, feature_states))
        remote_config_feature_state = next(filter(lambda fs: fs.feature == remote_config, feature_states))
        assert feature_flag_state.enabled
        assert remote_config_feature_state.get_feature_state_value() == overridden_value

    def test_get_all_feature_states_for_identity_returns_correct_values_for_identity_not_matching_segment(self):
        # Given
        identity = Identity.objects.create(identifier='test-identity', environment=self.environment)

        segment = Segment.objects.create(name='Test segment', project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

        trait_key = 'trait-key'
        trait_value = 'trait-value'
        Condition.objects.create(rule=rule, property=trait_key, value=trait_value, operator=EQUAL)

        feature_flag = Feature.objects.create(name='test-feature-flag', project=self.project, type='FLAG')

        initial_value = 'initial-value'
        remote_config = Feature.objects.create(name='test-remote-config', project=self.project,
                                               initial_value=initial_value, type='CONFIG')

        FeatureSegment.objects.create(feature=feature_flag, segment=segment, environment=self.environment, enabled=True)
        overridden_value = 'overridden-value'
        FeatureSegment.objects.create(feature=remote_config, segment=segment, environment=self.environment,
                                      value=overridden_value, value_type=STRING)

        # When
        feature_states = identity.get_all_feature_states()

        # Then
        feature_flag_state = next(filter(lambda fs: fs.feature == feature_flag, feature_states))
        remote_config_feature_state = next(filter(lambda fs: fs.feature == remote_config, feature_states))
        assert not feature_flag_state.enabled
        assert remote_config_feature_state.get_feature_state_value() == initial_value

    def test_get_all_feature_states_for_identity_returns_correct_value_for_matching_segment_when_value_integer(self):
        # Given
        trait_key = 'trait-key'
        trait_value = 'trait-value'
        identity = Identity.objects.create(identifier='test-identity', environment=self.environment)
        Trait.objects.create(identity=identity, trait_key=trait_key, string_value=trait_value)

        segment = Segment.objects.create(name='Test segment', project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(rule=rule, property=trait_key, value=trait_value, operator=EQUAL)

        remote_config = Feature.objects.create(name='test-remote-config', project=self.project,
                                               initial_value='initial-value', type='CONFIG')

        # Feature segment value is converted to string in the serializer so we set as a string value here to test
        # bool value
        overridden_value = '12'
        FeatureSegment.objects.create(feature=remote_config, segment=segment, environment=self.environment,
                                      value=overridden_value, value_type=INTEGER)

        # When
        feature_states = identity.get_all_feature_states()

        # Then
        feature_state = next(filter(lambda fs: fs.feature == remote_config, feature_states))
        assert feature_state.get_feature_state_value() == int(overridden_value)

    def test_get_all_feature_states_for_identity_returns_correct_value_for_matching_segment_when_value_boolean(self):
        # Given
        trait_key = 'trait-key'
        trait_value = 'trait-value'
        identity = Identity.objects.create(identifier='test-identity', environment=self.environment)
        Trait.objects.create(identity=identity, trait_key=trait_key, string_value=trait_value)

        segment = Segment.objects.create(name='Test segment', project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(rule=rule, property=trait_key, value=trait_value, operator=EQUAL)

        remote_config = Feature.objects.create(name='test-remote-config', project=self.project,
                                               initial_value='initial-value', type='CONFIG')

        # Feature segment value is converted to string in the serializer so we set as a string value here to test
        # bool value
        overridden_value = 'false'
        FeatureSegment.objects.create(feature=remote_config, segment=segment, environment=self.environment,
                                      value=overridden_value, value_type=BOOLEAN)

        # When
        feature_states = identity.get_all_feature_states()

        # Then
        feature_state = next(filter(lambda fs: fs.feature == remote_config, feature_states))
        assert not feature_state.get_feature_state_value()

    def test_get_all_feature_states_highest_value_of_highest_priority_segment(self):
        # Given - an identity with a trait that has an integer value of 10
        trait_key = 'trait-key'
        trait_value = 10
        identity = Identity.objects.create(identifier='test-identity', environment=self.environment)
        Trait.objects.create(identity=identity, trait_key=trait_key, integer_value=trait_value, value_type=INTEGER)

        # and a segment that matches all identities with a trait value greater than or equal to 5
        segment_1 = Segment.objects.create(name='Test segment 1', project=self.project)
        rule = SegmentRule.objects.create(segment=segment_1, type=SegmentRule.ALL_RULE)
        Condition.objects.create(rule=rule, property=trait_key, value=5, operator=GREATER_THAN_INCLUSIVE)

        # and another segment that matches all identities with a trait value greater than or equal to 10
        segment_2 = Segment.objects.create(name='Test segment 1', project=self.project)
        rule = SegmentRule.objects.create(segment=segment_2, type=SegmentRule.ALL_RULE)
        Condition.objects.create(rule=rule, property=trait_key, value=10, operator=GREATER_THAN_INCLUSIVE)

        # and a remote config feature
        initial_value = 'initial-value'
        remote_config = Feature.objects.create(name='test-remote-config', project=self.project,
                                               initial_value=initial_value, type='CONFIG')

        # which is overridden by both segments with different values
        overridden_value_1 = 'overridden-value-1'
        FeatureSegment.objects.create(feature=remote_config, segment=segment_1, environment=self.environment,
                                      value=overridden_value_1, value_type=STRING, priority=1)

        overridden_value_2 = 'overridden-value-2'
        FeatureSegment.objects.create(feature=remote_config, segment=segment_2, environment=self.environment,
                                      value=overridden_value_2, value_type=STRING, priority=2)

        # When - we get all feature states for an identity
        feature_states = identity.get_all_feature_states()

        # Then - only the flag associated with the highest priority feature segment is returned
        assert len(feature_states) == 1
        remote_config_feature_state = next(filter(lambda fs: fs.feature == remote_config, feature_states))
        assert remote_config_feature_state.get_feature_state_value() == overridden_value_1

    def test_remote_config_override(self):
        """specific test for bug raised following work to make feature segments unique to an environment"""
        # GIVEN - an identity with a trait that has a value of 10
        identity = Identity.objects.create(identifier="test", environment=self.environment)
        trait = Trait.objects.create(identity=identity, trait_key="my_trait", integer_value=10, value_type=INTEGER)

        # and a segment that matches users that have a value for this trait greater than 5
        segment = Segment.objects.create(name="Test segment", project=self.project)
        segment_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        condition = Condition.objects.create(
            rule=segment_rule, operator=GREATER_THAN, value="5", property=trait.trait_key
        )

        # and a feature that has a segment override in the same environment as the identity
        remote_config = Feature.objects.create(name="my_feature", initial_value="initial value", project=self.project)
        feature_segment = FeatureSegment.objects.create(
            feature=remote_config,
            environment=self.environment,
            segment=segment,
            value="overridden value 1",
            value_type=STRING
        )

        # WHEN - the value on the feature segment is updated and we get all the feature states for the identity
        feature_segment.value = "overridden value 2"
        feature_segment.save()
        feature_states = identity.get_all_feature_states()

        # THEN - the feature state value is correctly set to the newly updated feature segment value
        assert len(feature_states) == 1

        overridden_feature_state = feature_states[0]
        assert overridden_feature_state.get_feature_state_value() == feature_segment.value

