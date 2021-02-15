from django.test import TransactionTestCase

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import FLOAT, Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.utils import BOOLEAN, INTEGER, STRING
from organisations.models import Organisation
from projects.models import Project
from segments.models import (
    EQUAL,
    GREATER_THAN,
    GREATER_THAN_INCLUSIVE,
    LESS_THAN_INCLUSIVE,
    Condition,
    Segment,
    SegmentRule,
)

from .helpers import (
    create_trait_for_identity,
    generate_trait_data_item,
    get_trait_from_list_by_key,
)


class IdentityTestCase(TransactionTestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Test Org")
        self.project = Project.objects.create(
            name="Test Project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            name="Test Environment", project=self.project
        )

    def test_create_identity_should_assign_relevant_attributes(self):
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )

        assert isinstance(identity.environment, Environment)
        assert hasattr(identity, "created_date")

    def test_get_all_feature_states(self):
        feature = Feature.objects.create(name="Test Feature", project=self.project)
        feature_2 = Feature.objects.create(name="Test Feature 2", project=self.project)
        environment_2 = Environment.objects.create(
            name="Test Environment 2", project=self.project
        )

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
        # Given
        # a project with hide_disabled_flags enabled
        project_flag_disabled = Project.objects.create(
            name="Project Flag Disabled",
            organisation=self.organisation,
            hide_disabled_flags=True,
        )

        # and a set of features and environments for that project
        feature = Feature.objects.create(
            name="Test Feature", project=project_flag_disabled
        )
        feature_2 = Feature.objects.create(
            name="Test Feature 2", project=project_flag_disabled
        )
        other_environment = Environment.objects.create(
            name="Test Environment 2", project=project_flag_disabled
        )

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
        disabled_flag = FeatureState.objects.create(
            feature=feature_2,
            environment=other_environment,
            enabled=False,
            identity=identity_1,
        )
        FeatureState.objects.create(
            feature=feature,
            environment=self.environment,
            identity=identity_2,
        )

        # When
        # we get all flags for an environment
        env_flags = FeatureState.objects.filter(environment=other_environment)

        # And
        # we get flags for identity
        identity_flags = identity_1.get_all_feature_states()

        # Then
        # disabled flags are in environment flags
        assert disabled_flag in env_flags

        # But
        # not returned for identity
        assert disabled_flag not in identity_flags

        # And
        # identity flags are in environment flags
        for flag in identity_flags:
            assert flag in env_flags

    def test_create_trait_should_assign_relevant_attributes(self):
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )
        trait = Trait.objects.create(
            trait_key="test-key", string_value="testing trait", identity=identity
        )

        self.assertIsInstance(trait.identity, Identity)
        self.assertTrue(hasattr(trait, "trait_key"))
        self.assertTrue(hasattr(trait, "value_type"))
        self.assertTrue(hasattr(trait, "created_date"))

    def test_create_trait_float_value_should_assign_relevant_attributes(self):
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )
        float_value = 10.5
        trait = Trait.objects.create(
            trait_key="test-float",
            float_value=float_value,
            identity=identity,
            value_type=FLOAT,
        )

        self.assertIsInstance(trait.identity, Identity)
        self.assertTrue(hasattr(trait, "trait_key"))
        self.assertTrue(hasattr(trait, "float_value"))
        self.assertTrue(float_value == trait.float_value)
        self.assertTrue(hasattr(trait, "value_type"))
        self.assertTrue(trait.value_type == FLOAT)
        self.assertTrue(hasattr(trait, "created_date"))

    def test_on_update_trait_should_update_relevant_attributes(self):
        identity = Identity.objects.create(
            identifier="test-identifier", environment=self.environment
        )
        trait = Trait.objects.create(
            trait_key="test-key", string_value="testing trait", identity=identity
        )

        # TODO: need tests for updates

    def test_get_all_traits_for_identity(self):
        identity = Identity.objects.create(
            identifier="test-identifier", environment=self.environment
        )
        identity2 = Identity.objects.create(
            identifier="test-identity_two", environment=self.environment
        )

        Trait.objects.create(
            trait_key="test-key-one", string_value="testing trait", identity=identity
        )
        Trait.objects.create(
            trait_key="test-key-two", string_value="testing trait", identity=identity
        )
        Trait.objects.create(
            trait_key="test-key-three", string_value="testing trait", identity=identity
        )
        Trait.objects.create(
            trait_key="test-key-three", string_value="testing trait", identity=identity2
        )

        # Identity one should have 3
        traits_identity_one = identity.get_all_user_traits()
        self.assertEqual(len(traits_identity_one), 3)

        traits_identity_two = identity2.get_all_user_traits()
        self.assertEqual(len(traits_identity_two), 1)

    def test_get_all_feature_states_for_identity_returns_correct_values_for_matching_segment(
        self,
    ):
        # Given
        trait_key = "trait-key"
        trait_value = "trait-value"
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )
        Trait.objects.create(
            identity=identity, trait_key=trait_key, string_value=trait_value
        )

        segment = Segment.objects.create(name="Test segment", project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(
            rule=rule, property=trait_key, value=trait_value, operator=EQUAL
        )

        feature_flag = Feature.objects.create(
            name="test-feature-flag", project=self.project, type="FLAG"
        )
        remote_config = Feature.objects.create(
            name="test-remote-config",
            project=self.project,
            initial_value="initial-value",
            type="CONFIG",
        )

        FeatureSegment.objects.create(
            feature=feature_flag,
            segment=segment,
            environment=self.environment,
            enabled=True,
        )
        overridden_value = "overridden-value"
        FeatureSegment.objects.create(
            feature=remote_config,
            segment=segment,
            environment=self.environment,
            value=overridden_value,
            value_type=STRING,
        )

        # When
        feature_states = identity.get_all_feature_states()

        # Then
        feature_flag_state = next(
            filter(lambda fs: fs.feature == feature_flag, feature_states)
        )
        remote_config_feature_state = next(
            filter(lambda fs: fs.feature == remote_config, feature_states)
        )
        assert feature_flag_state.enabled
        assert remote_config_feature_state.get_feature_state_value() == overridden_value

    def test_get_all_feature_states_for_identity_returns_correct_values_for_identity_not_matching_segment(
        self,
    ):
        # Given
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )

        segment = Segment.objects.create(name="Test segment", project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

        trait_key = "trait-key"
        trait_value = "trait-value"
        Condition.objects.create(
            rule=rule, property=trait_key, value=trait_value, operator=EQUAL
        )

        feature_flag = Feature.objects.create(
            name="test-feature-flag", project=self.project, type="FLAG"
        )

        initial_value = "initial-value"
        remote_config = Feature.objects.create(
            name="test-remote-config",
            project=self.project,
            initial_value=initial_value,
            type="CONFIG",
        )

        FeatureSegment.objects.create(
            feature=feature_flag,
            segment=segment,
            environment=self.environment,
            enabled=True,
        )
        overridden_value = "overridden-value"
        FeatureSegment.objects.create(
            feature=remote_config,
            segment=segment,
            environment=self.environment,
            value=overridden_value,
            value_type=STRING,
        )

        # When
        feature_states = identity.get_all_feature_states()

        # Then
        feature_flag_state = next(
            filter(lambda fs: fs.feature == feature_flag, feature_states)
        )
        remote_config_feature_state = next(
            filter(lambda fs: fs.feature == remote_config, feature_states)
        )
        assert not feature_flag_state.enabled
        assert remote_config_feature_state.get_feature_state_value() == initial_value

    def test_get_all_feature_states_for_identity_returns_correct_value_for_matching_segment_when_value_integer(
        self,
    ):
        # Given
        trait_key = "trait-key"
        trait_value = "trait-value"
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )
        Trait.objects.create(
            identity=identity, trait_key=trait_key, string_value=trait_value
        )

        segment = Segment.objects.create(name="Test segment", project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(
            rule=rule, property=trait_key, value=trait_value, operator=EQUAL
        )

        remote_config = Feature.objects.create(
            name="test-remote-config",
            project=self.project,
            initial_value="initial-value",
            type="CONFIG",
        )

        # Feature segment value is converted to string in the serializer so we set as a string value here to test
        # bool value
        overridden_value = "12"
        FeatureSegment.objects.create(
            feature=remote_config,
            segment=segment,
            environment=self.environment,
            value=overridden_value,
            value_type=INTEGER,
        )

        # When
        feature_states = identity.get_all_feature_states()

        # Then
        feature_state = next(
            filter(lambda fs: fs.feature == remote_config, feature_states)
        )
        assert feature_state.get_feature_state_value() == int(overridden_value)

    def test_get_all_feature_states_for_identity_returns_correct_value_for_matching_segment_when_value_boolean(
        self,
    ):
        # Given
        trait_key = "trait-key"
        trait_value = "trait-value"
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )
        Trait.objects.create(
            identity=identity, trait_key=trait_key, string_value=trait_value
        )

        segment = Segment.objects.create(name="Test segment", project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(
            rule=rule, property=trait_key, value=trait_value, operator=EQUAL
        )

        remote_config = Feature.objects.create(
            name="test-remote-config",
            project=self.project,
            initial_value="initial-value",
            type="CONFIG",
        )

        # Feature segment value is converted to string in the serializer so we set as a string value here to test
        # bool value
        overridden_value = "false"
        FeatureSegment.objects.create(
            feature=remote_config,
            segment=segment,
            environment=self.environment,
            value=overridden_value,
            value_type=BOOLEAN,
        )

        # When
        feature_states = identity.get_all_feature_states()

        # Then
        feature_state = next(
            filter(lambda fs: fs.feature == remote_config, feature_states)
        )
        assert not feature_state.get_feature_state_value()

    def test_get_all_feature_states_for_identity_returns_correct_values_for_matching_segment_when_value_float(
        self,
    ):
        # Given
        trait_key = "trait-key"
        trait_value = 10.5
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )
        trait = Trait.objects.create(
            identity=identity,
            trait_key=trait_key,
            float_value=trait_value,
            value_type=FLOAT,
        )

        segment = Segment.objects.create(name="Test segment", project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(
            rule=rule, property=trait_key, value=trait_value, operator=EQUAL
        )

        feature_flag = Feature.objects.create(
            name="test-remote-config",
            project=self.project,
            initial_value="initial-value",
            type="FLAG",
        )

        FeatureSegment.objects.create(
            feature=feature_flag,
            segment=segment,
            environment=self.environment,
            enabled=True,
        )

        # When
        feature_states = identity.get_all_feature_states()
        user_traits = identity.get_all_user_traits()

        # Then
        feature_state = next(
            filter(lambda fs: fs.feature == feature_flag, feature_states)
        )
        assert feature_state.enabled is True
        assert user_traits[0].float_value == trait_value

    def test_get_all_feature_states_highest_value_of_highest_priority_segment(self):
        # Given - an identity with a trait that has an integer value of 10
        trait_key = "trait-key"
        trait_value = 10
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )
        Trait.objects.create(
            identity=identity,
            trait_key=trait_key,
            integer_value=trait_value,
            value_type=INTEGER,
        )

        # and a segment that matches all identities with a trait value greater than or equal to 5
        segment_1 = Segment.objects.create(name="Test segment 1", project=self.project)
        rule = SegmentRule.objects.create(segment=segment_1, type=SegmentRule.ALL_RULE)
        Condition.objects.create(
            rule=rule, property=trait_key, value=5, operator=GREATER_THAN_INCLUSIVE
        )

        # and another segment that matches all identities with a trait value greater than or equal to 10
        segment_2 = Segment.objects.create(name="Test segment 1", project=self.project)
        rule = SegmentRule.objects.create(segment=segment_2, type=SegmentRule.ALL_RULE)
        Condition.objects.create(
            rule=rule, property=trait_key, value=10, operator=GREATER_THAN_INCLUSIVE
        )

        # and a remote config feature
        initial_value = "initial-value"
        remote_config = Feature.objects.create(
            name="test-remote-config",
            project=self.project,
            initial_value=initial_value,
            type="CONFIG",
        )

        # which is overridden by both segments with different values
        overridden_value_1 = "overridden-value-1"
        FeatureSegment.objects.create(
            feature=remote_config,
            segment=segment_1,
            environment=self.environment,
            value=overridden_value_1,
            value_type=STRING,
            priority=1,
        )

        overridden_value_2 = "overridden-value-2"
        FeatureSegment.objects.create(
            feature=remote_config,
            segment=segment_2,
            environment=self.environment,
            value=overridden_value_2,
            value_type=STRING,
            priority=2,
        )

        # When - we get all feature states for an identity
        feature_states = identity.get_all_feature_states()

        # Then - only the flag associated with the highest priority feature segment is returned
        assert len(feature_states) == 1
        remote_config_feature_state = next(
            filter(lambda fs: fs.feature == remote_config, feature_states)
        )
        assert (
            remote_config_feature_state.get_feature_state_value() == overridden_value_1
        )

    def test_remote_config_override(self):
        """specific test for bug raised following work to make feature segments unique to an environment"""
        # GIVEN - an identity with a trait that has a value of 10
        identity = Identity.objects.create(
            identifier="test", environment=self.environment
        )
        trait = Trait.objects.create(
            identity=identity,
            trait_key="my_trait",
            integer_value=10,
            value_type=INTEGER,
        )

        # and a segment that matches users that have a value for this trait greater than 5
        segment = Segment.objects.create(name="Test segment", project=self.project)
        segment_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        condition = Condition.objects.create(
            rule=segment_rule,
            operator=GREATER_THAN,
            value="5",
            property=trait.trait_key,
        )

        # and a feature that has a segment override in the same environment as the identity
        remote_config = Feature.objects.create(
            name="my_feature", initial_value="initial value", project=self.project
        )
        feature_segment = FeatureSegment.objects.create(
            feature=remote_config,
            environment=self.environment,
            segment=segment,
            value="overridden value 1",
            value_type=STRING,
        )

        # WHEN - the value on the feature segment is updated and we get all the feature states for the identity
        feature_segment.value = "overridden value 2"
        feature_segment.save()
        feature_states = identity.get_all_feature_states()

        # THEN - the feature state value is correctly set to the newly updated feature segment value
        assert len(feature_states) == 1

        overridden_feature_state = feature_states[0]
        assert (
            overridden_feature_state.get_feature_state_value() == feature_segment.value
        )

    def test_get_all_feature_states_returns_correct_value_when_traits_passed_manually(
        self,
    ):
        """
        Verify that when traits are passed manually, then the segments are correctly
        analysed for the identity and the correct value is returned for the feature
        state.
        """
        # Given - an identity with a trait that has an integer value of 10
        trait_key = "trait-key"
        trait_value = 10
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )
        trait = Trait(
            identity=identity,
            trait_key=trait_key,
            integer_value=trait_value,
            value_type=INTEGER,
        )

        # and a segment that matches all identities with a trait value greater than or equal to 5
        segment = Segment.objects.create(name="Test segment 1", project=self.project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(
            rule=rule, property=trait_key, value=5, operator=GREATER_THAN_INCLUSIVE
        )

        # and a feature flag
        default_state = False
        feature_flag = Feature.objects.create(
            project=self.project, name="test_flag", default_enabled=default_state
        )

        # which is overridden by the segment
        enabled_for_segment = not default_state
        FeatureSegment.objects.create(
            feature=feature_flag,
            segment=segment,
            environment=self.environment,
            priority=1,
            enabled=enabled_for_segment,
        )

        # When - we get all feature states for an identity
        feature_states = identity.get_all_feature_states(traits=[trait])

        # Then - the flag is returned with the correct state
        assert len(feature_states) == 1
        assert feature_states[0].enabled == enabled_for_segment

    def test_generate_traits_with_persistence(self):
        # Given
        identity = Identity.objects.create(
            identifier="identifier", environment=self.environment
        )
        trait_data_items = [
            generate_trait_data_item("string_trait", "string_value"),
            generate_trait_data_item("integer_trait", 1),
            generate_trait_data_item("boolean_value", True),
        ]

        # When
        trait_models = identity.generate_traits(trait_data_items, persist=True)

        # Then
        # the response from the method has 3 traits
        assert len(trait_models) == 3

        # and the database matches it
        assert Trait.objects.filter(identity=identity).count() == 3

    def test_generate_traits_without_persistence(self):
        # Given
        identity = Identity.objects.create(
            identifier="identifier", environment=self.environment
        )
        trait_data_items = [
            generate_trait_data_item("string_trait", "string_value"),
            generate_trait_data_item("integer_trait", 1),
            generate_trait_data_item("boolean_value", True),
        ]

        # When
        trait_models = identity.generate_traits(trait_data_items, persist=False)

        # Then
        # the response from the method has 3 traits
        assert len(trait_models) == 3
        # and they are all Trait objects
        assert all([isinstance(trait, Trait) for trait in trait_models])

        # but the database has none
        assert Trait.objects.filter(identity=identity).count() == 0

    def test_update_traits(self):
        """
        This is quite a long test to verify the update traits functionality correctly
        handles updating and creating traits.
        """
        # Given
        # an identity
        identity = Identity.objects.create(
            identifier="identifier", environment=self.environment
        )

        # that already has 2 traits
        trait_1_key = "trait_1"
        trait_1_value = 1
        trait_2_key = "trait_2"
        trait_2_value = 2
        trait_1 = create_trait_for_identity(identity, trait_1_key, trait_1_value)
        trait_2 = create_trait_for_identity(identity, trait_2_key, trait_2_value)

        # and a list of trait data items that should end up creating 1 additional
        # trait, updating 1 and leaving another alone but returning it as it is
        new_trait_1_value = 5
        trait_3_key = "trait_3"
        trait_3_value = 3
        trait_data_items = [
            generate_trait_data_item(
                trait_key=trait_1.trait_key, trait_value=new_trait_1_value
            ),
            generate_trait_data_item(trait_key=trait_3_key, trait_value=trait_3_value),
        ]

        # When
        updated_traits = identity.update_traits(trait_data_items)

        # Then
        # 3 traits are returned
        assert len(updated_traits) == 3

        # and the first trait has it's value updated correctly
        updated_trait_1 = get_trait_from_list_by_key(trait_1_key, updated_traits)
        assert updated_trait_1.trait_value == new_trait_1_value

        # and the second trait is left untouched and returned as is
        updated_trait_2 = get_trait_from_list_by_key(trait_2_key, updated_traits)
        assert updated_trait_2.trait_value == trait_2_value

        # and the third trait is created correctly
        updated_trait_3 = get_trait_from_list_by_key(trait_3_key, updated_traits)
        assert updated_trait_3.trait_value == trait_3_value

    def test_update_traits_deletes_when_nulled_out(self):
        """
        This is quite a long test to verify the update traits functionality correctly
        handles updating and creating traits.
        """
        # Given
        # an identity
        identity = Identity.objects.create(
            identifier="identifier", environment=self.environment
        )

        # that already has 2 traits
        trait_1_key = "trait_1"
        trait_1_value = 1
        trait_2_key = "trait_2"
        trait_2_value = 2
        create_trait_for_identity(identity, trait_1_key, trait_1_value)
        create_trait_for_identity(identity, trait_2_key, trait_2_value)

        # and a list of trait data items that should delete 1 and leave the other
        trait_data_items = [
            generate_trait_data_item(trait_key=trait_1_key, trait_value=None)
        ]

        # When
        updated_traits = identity.update_traits(trait_data_items)

        # Then
        # 1 trait is returned
        assert len(updated_traits) == 1

        # and the nulled out trait has been deleted
        assert not Trait.objects.filter(
            trait_key=trait_1_key, identity=identity
        ).exists()

        # and the returned trait is untouched
        assert updated_traits[0].trait_key == trait_2_key
        assert updated_traits[0].trait_value == trait_2_value

    def test_get_segments(self):
        # Given
        # a segment with multiple rules and conditions
        segment = Segment.objects.create(name="Test Segment", project=self.project)

        rule_one = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ANY_RULE
        )
        Condition.objects.create(
            rule=rule_one, operator=EQUAL, property="foo", value="bar"
        )
        Condition.objects.create(
            rule=rule_one, operator=EQUAL, property="foo", value="baz"
        )

        rule_two = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        Condition.objects.create(
            rule=rule_two, operator=GREATER_THAN_INCLUSIVE, property="bar", value=10
        )
        Condition.objects.create(
            rule=rule_two, operator=LESS_THAN_INCLUSIVE, property="bar", value=20
        )

        # and an identity with traits that match the segment
        identity = Identity.objects.create(
            identifier="identity-1", environment=self.environment
        )
        Trait.objects.create(
            identity=identity, trait_key="bar", value_type=INTEGER, integer_value=15
        )
        Trait.objects.create(
            identity=identity, trait_key="foo", value_type=STRING, string_value="bar"
        )

        # When
        # we get the matching segments for an identity
        with self.assertNumQueries(5):
            segments = identity.get_segments()

        # Then
        # the number of queries are what we expect (see above context manager) and the segment is returned
        assert len(segments) == 1 and segments[0] == segment
