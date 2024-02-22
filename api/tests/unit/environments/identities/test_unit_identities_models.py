import pytest
from core.constants import FLOAT
from django.utils import timezone
from flag_engine.segments.constants import (
    EQUAL,
    GREATER_THAN,
    GREATER_THAN_INCLUSIVE,
    LESS_THAN_INCLUSIVE,
    NOT_EQUAL,
)
from pytest_django import DjangoAssertNumQueries

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from features.models import (
    Feature,
    FeatureSegment,
    FeatureState,
    FeatureStateValue,
)
from features.value_types import BOOLEAN, INTEGER, STRING
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule

from .helpers import (
    create_trait_for_identity,
    generate_trait_data_item,
    get_trait_from_list_by_key,
)


def test_create_identity_should_assign_relevant_attributes(
    environment: Environment,
) -> None:
    # When
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )

    # Then
    assert isinstance(identity.environment, Environment)
    assert hasattr(identity, "created_date")


def test_get_all_feature_states(
    project: Project,
    environment: Environment,
) -> None:
    feature = Feature.objects.create(name="Test Feature", project=project)
    feature_2 = Feature.objects.create(name="Test Feature 2", project=project)
    environment_2 = Environment.objects.create(
        name="Test Environment 2", project=project
    )

    identity_1 = Identity.objects.create(
        identifier="test-identity-1",
        environment=environment,
    )
    identity_2 = Identity.objects.create(
        identifier="test-identity-2",
        environment=environment,
    )
    identity_3 = Identity.objects.create(
        identifier="test-identity-3",
        environment=environment_2,
    )

    # User unassigned - automatically should be created via `Feature` save method.
    fs_environment_anticipated = FeatureState.objects.get(
        feature=feature_2,
        environment=environment,
    )

    # User assigned
    fs_identity_anticipated = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        identity=identity_1,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
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
    assert len(flags) == 2
    assert fs_environment_anticipated in flags
    assert fs_identity_anticipated in flags


def test_create_trait_should_assign_relevant_attributes(
    environment: Environment,
) -> None:
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )
    trait = Trait.objects.create(
        trait_key="test-key", string_value="testing trait", identity=identity
    )

    assert isinstance(trait.identity, Identity)
    assert hasattr(trait, "trait_key") is True
    assert hasattr(trait, "value_type") is True
    assert hasattr(trait, "created_date") is True


def test_create_trait_float_value_should_assign_relevant_attributes(
    environment: Environment,
) -> None:
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )
    float_value = 10.5
    trait = Trait.objects.create(
        trait_key="test-float",
        float_value=float_value,
        identity=identity,
        value_type=FLOAT,
    )

    assert isinstance(trait.identity, Identity) is True
    assert hasattr(trait, "trait_key") is True
    assert hasattr(trait, "float_value") is True
    assert float_value == trait.float_value
    assert hasattr(trait, "value_type") is True
    assert trait.value_type == FLOAT
    assert hasattr(trait, "created_date") is True


def test_get_all_traits_for_identity(environment: Environment) -> None:
    identity = Identity.objects.create(
        identifier="test-identifier", environment=environment
    )
    identity2 = Identity.objects.create(
        identifier="test-identity_two", environment=environment
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
    assert len(traits_identity_one) == 3

    traits_identity_two = identity2.get_all_user_traits()
    assert len(traits_identity_two) == 1


def test_get_all_feature_states_for_identity_returns_correct_values_for_matching_segment(
    environment: Environment,
    project: Project,
) -> None:
    # Given
    trait_key = "trait-key"
    trait_value = "trait-value"
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )
    Trait.objects.create(
        identity=identity, trait_key=trait_key, string_value=trait_value
    )

    segment = Segment.objects.create(name="Test segment", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule, property=trait_key, value=trait_value, operator=EQUAL
    )

    feature_flag = Feature.objects.create(
        name="test-feature-flag", project=project, type="FLAG"
    )
    remote_config = Feature.objects.create(
        name="test-remote-config",
        project=project,
        initial_value="initial-value",
        type="CONFIG",
    )

    feature_flag_feature_segment = FeatureSegment.objects.create(
        feature=feature_flag,
        segment=segment,
        environment=environment,
    )
    FeatureState.objects.create(
        feature=feature_flag,
        feature_segment=feature_flag_feature_segment,
        environment=environment,
        enabled=True,
    )

    overridden_value = "overridden-value"
    remote_config_feature_segment = FeatureSegment.objects.create(
        feature=remote_config, segment=segment, environment=environment
    )
    feature_state = FeatureState.objects.create(
        feature_segment=remote_config_feature_segment,
        feature=remote_config,
        environment=environment,
    )
    FeatureStateValue.objects.filter(feature_state=feature_state).update(
        string_value=overridden_value
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
    assert feature_flag_state.enabled is True
    assert remote_config_feature_state.get_feature_state_value() == overridden_value


def test_get_all_feature_states_for_identity_returns_correct_values_for_identity_not_matching_segment(
    environment: Environment,
    project: Project,
) -> None:
    # Given
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )

    segment = Segment.objects.create(name="Test segment", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

    trait_key = "trait-key"
    trait_value = "trait-value"
    Condition.objects.create(
        rule=rule, property=trait_key, value=trait_value, operator=EQUAL
    )

    feature_flag = Feature.objects.create(
        name="test-feature-flag", project=project, type="FLAG"
    )

    initial_value = "initial-value"
    remote_config = Feature.objects.create(
        name="test-remote-config",
        project=project,
        initial_value=initial_value,
        type="CONFIG",
    )

    FeatureSegment.objects.create(
        feature=feature_flag,
        segment=segment,
        environment=environment,
    )
    overridden_value = "overridden-value"
    feature_segment = FeatureSegment.objects.create(
        feature=remote_config, segment=segment, environment=environment
    )
    segment_feature_state = FeatureState.objects.create(
        feature=remote_config,
        feature_segment=feature_segment,
        environment=environment,
    )
    FeatureStateValue.objects.filter(feature_state=segment_feature_state).update(
        string_value=overridden_value
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
    environment: Environment,
    project: Project,
) -> None:
    # Given
    trait_key = "trait-key"
    trait_value = "trait-value"
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )
    Trait.objects.create(
        identity=identity, trait_key=trait_key, string_value=trait_value
    )

    segment = Segment.objects.create(name="Test segment", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule, property=trait_key, value=trait_value, operator=EQUAL
    )

    remote_config = Feature.objects.create(
        name="test-remote-config",
        project=project,
        initial_value="initial-value",
        type="CONFIG",
    )

    # Feature segment value is converted to string in the
    # serializer so we set as a string value here to test bool
    overridden_value = 12
    feature_segment = FeatureSegment.objects.create(
        feature=remote_config, segment=segment, environment=environment
    )
    segment_feature_state = FeatureState.objects.create(
        feature=remote_config,
        feature_segment=feature_segment,
        environment=environment,
    )
    FeatureStateValue.objects.filter(feature_state=segment_feature_state).update(
        integer_value=overridden_value, type=INTEGER
    )

    # When
    feature_states = identity.get_all_feature_states()

    # Then
    feature_state = next(filter(lambda fs: fs.feature == remote_config, feature_states))
    assert feature_state.get_feature_state_value() == overridden_value


def test_get_all_feature_states_for_identity_returns_correct_value_for_matching_segment_when_value_boolean(
    environment: Environment,
    project: Project,
) -> None:
    # Given
    trait_key = "trait-key"
    trait_value = "trait-value"
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )
    Trait.objects.create(
        identity=identity, trait_key=trait_key, string_value=trait_value
    )

    segment = Segment.objects.create(name="Test segment", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule, property=trait_key, value=trait_value, operator=EQUAL
    )

    remote_config = Feature.objects.create(
        name="test-remote-config",
        project=project,
        initial_value="initial-value",
        type="CONFIG",
    )

    # Feature segment value is converted to string in the serializer so we set as a string value here to test
    # bool value
    overridden_value = False
    feature_segment = FeatureSegment.objects.create(
        feature=remote_config, segment=segment, environment=environment
    )
    feature_state = FeatureState.objects.create(
        feature=remote_config,
        feature_segment=feature_segment,
        environment=environment,
    )
    FeatureStateValue.objects.filter(feature_state=feature_state).update(
        boolean_value=overridden_value, type=BOOLEAN
    )

    # When
    feature_states = identity.get_all_feature_states()

    # Then
    feature_state = next(filter(lambda fs: fs.feature == remote_config, feature_states))
    assert not feature_state.get_feature_state_value()


def test_get_all_feature_states_highest_value_of_highest_priority_segment(
    environment: Environment,
    project: Project,
) -> None:
    # Given - an identity with a trait that has an integer value of 10
    trait_key = "trait-key"
    trait_value = 10
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )
    Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        integer_value=trait_value,
        value_type=INTEGER,
    )

    # and a segment that matches all identities with a trait value greater than or equal to 5
    segment_1 = Segment.objects.create(name="Test segment 1", project=project)
    rule = SegmentRule.objects.create(segment=segment_1, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule, property=trait_key, value=5, operator=GREATER_THAN_INCLUSIVE
    )

    # and another segment that matches all identities with a trait value greater than or equal to 10
    segment_2 = Segment.objects.create(name="Test segment 1", project=project)
    rule = SegmentRule.objects.create(segment=segment_2, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule, property=trait_key, value=10, operator=GREATER_THAN_INCLUSIVE
    )

    # and a remote config feature
    initial_value = "initial-value"
    remote_config = Feature.objects.create(
        name="test-remote-config",
        project=project,
        initial_value=initial_value,
        type="CONFIG",
    )

    # which is overridden by both segments with different values
    overridden_value_1 = "overridden-value-1"
    feature_segment_1 = FeatureSegment.objects.create(
        feature=remote_config,
        segment=segment_1,
        environment=environment,
        priority=1,
    )
    segment_feature_state_1 = FeatureState.objects.create(
        feature=remote_config,
        feature_segment=feature_segment_1,
        environment=environment,
    )
    FeatureStateValue.objects.filter(feature_state=segment_feature_state_1).update(
        string_value=overridden_value_1, type=STRING
    )

    overridden_value_2 = "overridden-value-2"
    feature_segment_2 = FeatureSegment.objects.create(
        feature=remote_config,
        segment=segment_2,
        environment=environment,
        priority=2,
    )
    segment_feature_state_2 = FeatureState.objects.create(
        feature=remote_config,
        feature_segment=feature_segment_2,
        environment=environment,
    )
    FeatureStateValue.objects.filter(feature_state=segment_feature_state_2).update(
        string_value=overridden_value_2, type=STRING
    )

    # When - we get all feature states for an identity
    feature_states = identity.get_all_feature_states()

    # Then - only the flag associated with the highest priority feature segment is returned
    assert len(feature_states) == 1
    remote_config_feature_state = next(
        filter(lambda fs: fs.feature == remote_config, feature_states)
    )
    assert remote_config_feature_state.get_feature_state_value() == overridden_value_1


def test_remote_config_override(
    environment: Environment,
    project: Project,
) -> None:
    """specific test for bug raised following work to make feature segments unique to an environment"""
    # Given - an identity with a trait that has a value of 10
    identity = Identity.objects.create(identifier="test", environment=environment)
    trait = Trait.objects.create(
        identity=identity,
        trait_key="my_trait",
        integer_value=10,
        value_type=INTEGER,
    )

    # and a segment that matches users that have a value for this trait greater than 5
    segment = Segment.objects.create(name="Test segment", project=project)
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        rule=segment_rule,
        operator=GREATER_THAN,
        value="5",
        property=trait.trait_key,
    )

    # and a feature that has a segment override in the same environment as the identity
    remote_config = Feature.objects.create(
        name="my_feature", initial_value="initial value", project=project
    )
    overridden_value_1 = "overridden value 1"
    feature_segment = FeatureSegment.objects.create(
        feature=remote_config, environment=environment, segment=segment
    )
    segment_feature_state = FeatureState.objects.create(
        feature=remote_config,
        feature_segment=feature_segment,
        environment=environment,
    )
    FeatureStateValue.objects.filter(feature_state=segment_feature_state).update(
        string_value=overridden_value_1, type=STRING
    )

    # When - the value of the feature state attached to the feature segment is
    # updated and we get all the feature states for the identity
    overridden_value_2 = "overridden value 2"
    segment_feature_state.feature_state_value.string_value = overridden_value_2
    segment_feature_state.feature_state_value.save()
    feature_states = identity.get_all_feature_states()

    # Then - the feature state value is correctly set to the newly updated feature segment value
    assert len(feature_states) == 1

    overridden_feature_state = feature_states[0]
    assert overridden_feature_state.get_feature_state_value() == overridden_value_2


def test_get_all_feature_states_returns_correct_value_when_traits_passed_manually(
    environment: Environment,
    project: Project,
) -> None:
    """
    Verify that when traits are passed manually, then the segments are correctly
    analysed for the identity and the correct value is returned for the feature
    state.
    """

    # Given - an identity with a trait that has an integer value of 10
    trait_key = "trait-key"
    trait_value = 10
    identity = Identity.objects.create(
        identifier="test-identity", environment=environment
    )
    trait = Trait(
        identity=identity,
        trait_key=trait_key,
        integer_value=trait_value,
        value_type=INTEGER,
    )

    # and a segment that matches all identities with a trait value greater than or equal to 5
    segment = Segment.objects.create(name="Test segment 1", project=project)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule, property=trait_key, value=5, operator=GREATER_THAN_INCLUSIVE
    )

    # and a feature flag
    default_state = False
    feature_flag = Feature.objects.create(
        project=project, name="test_flag", default_enabled=default_state
    )

    # which is overridden by the segment
    enabled_for_segment = not default_state
    feature_segment = FeatureSegment.objects.create(
        feature=feature_flag,
        segment=segment,
        environment=environment,
        priority=1,
    )
    FeatureState.objects.create(
        feature=feature_flag,
        feature_segment=feature_segment,
        environment=environment,
        enabled=enabled_for_segment,
    )

    # When - we get all feature states for an identity
    feature_states = identity.get_all_feature_states(traits=[trait])

    # Then - the flag is returned with the correct state
    assert len(feature_states) == 1
    assert feature_states[0].enabled == enabled_for_segment


def test_generate_traits_with_persistence(environment: Environment) -> None:
    # Given
    identity = Identity.objects.create(identifier="identifier", environment=environment)
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


def test_generate_traits_without_persistence(environment: Environment) -> None:
    # Given
    identity = Identity.objects.create(identifier="identifier", environment=environment)

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


def test_update_traits(environment: Environment) -> None:
    """
    This is quite a long test to verify the update traits functionality correctly
    handles updating and creating traits.
    """
    # Given
    # an identity
    identity = Identity.objects.create(identifier="identifier", environment=environment)

    # that already has 2 traits
    trait_1_key = "trait_1"
    trait_1_value = 1
    trait_2_key = "trait_2"
    trait_2_value = 2
    trait_1 = create_trait_for_identity(identity, trait_1_key, trait_1_value)
    create_trait_for_identity(identity, trait_2_key, trait_2_value)

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


def test_update_traits_deletes_when_nulled_out(environment: Environment) -> None:
    """
    This is quite a long test to verify the update traits functionality correctly
    handles updating and creating traits.
    """
    # Given
    # an identity
    identity = Identity.objects.create(identifier="identifier", environment=environment)

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
    assert not Trait.objects.filter(trait_key=trait_1_key, identity=identity).exists()

    # and the returned trait is untouched
    assert updated_traits[0].trait_key == trait_2_key
    assert updated_traits[0].trait_value == trait_2_value


def test_get_identity_segments(
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
    project: Project,
) -> None:
    # Given
    # a segment with multiple rules and conditions
    segment = Segment.objects.create(name="Test Segment", project=project)

    rule_one = SegmentRule.objects.create(segment=segment, type=SegmentRule.ANY_RULE)
    Condition.objects.create(rule=rule_one, operator=EQUAL, property="foo", value="bar")
    Condition.objects.create(rule=rule_one, operator=EQUAL, property="foo", value="baz")

    rule_two = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule_two, operator=GREATER_THAN_INCLUSIVE, property="bar", value=10
    )
    Condition.objects.create(
        rule=rule_two, operator=LESS_THAN_INCLUSIVE, property="bar", value=20
    )

    # And nested rules to test the number of queries
    for i in range(50):
        property_name = "foo"
        nested_rule = SegmentRule.objects.create(
            rule=rule_two, type=SegmentRule.ALL_RULE
        )
        Condition.objects.create(
            rule=nested_rule,
            operator=NOT_EQUAL,
            property=property_name,
            value="some_other_value",
        )

    # and an identity with traits that match the segment
    identity = Identity.objects.create(identifier="identity-1", environment=environment)
    Trait.objects.create(
        identity=identity, trait_key="bar", value_type=INTEGER, integer_value=15
    )
    Trait.objects.create(
        identity=identity, trait_key="foo", value_type=STRING, string_value="bar"
    )

    # When
    # we get the matching segments for an identity
    with django_assert_num_queries(7):
        segments = identity.get_segments()

    # Then
    # the number of queries are what we expect (see above context manager) and
    # the segment is returned
    assert len(segments) == 1 and segments[0] == segment


def test_get_segments_with_overrides_only_only_returns_segments_overridden_in_environment(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    segment_1 = Segment.objects.create(name="Segment 1", project=project)
    segment_2 = Segment.objects.create(name="Segment 2", project=project)

    condition_property = "foo"
    condition_value = "bar"
    for segment in [segment_1, segment_2]:
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(
            operator=EQUAL,
            property=condition_property,
            value=condition_value,
            rule=rule,
        )

    feature = Feature.objects.create(name="test_feature", project=project)
    feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment_1, environment=environment
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
    )

    identity = Identity.objects.create(identifier="identity", environment=environment)
    Trait.objects.create(
        identity=identity,
        trait_key=condition_property,
        value_type=STRING,
        string_value=condition_value,
    )

    # When
    identity_segments = identity.get_segments(overrides_only=True)

    # Then
    assert len(identity_segments) == 1
    assert identity_segments[0] == segment_1


def test_get_all_feature_states_does_not_return_null_versions(
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    version_1_feature_state = FeatureState.objects.get(
        feature=feature, environment=environment
    )
    # clone the feature state with null version (using as_draft argument)
    version_1_feature_state.clone(
        env=environment, live_from=timezone.now(), as_draft=True
    )

    identity = Identity.objects.create(environment=environment, identifier="identity")

    # When
    identity_feature_states = identity.get_all_feature_states()

    # Then
    assert len(identity_feature_states) == 1
    assert identity_feature_states[0].id == version_1_feature_state.id


def test_update_traits_does_not_make_extra_queries_if_traits_value_do_not_change(
    identity, django_assert_num_queries, trait
):
    # Given
    trait_data_items = [
        generate_trait_data_item(
            trait_key=trait.trait_key, trait_value=trait.trait_value
        ),
    ]

    # When
    with django_assert_num_queries(1):
        identity.update_traits(trait_data_items)

    # Then - We only expect 1 query(for reading all the traits) should have been made


@pytest.mark.parametrize(
    "environment_value, project_value, disabled_flag_returned",
    (
        (True, True, False),
        (True, False, False),
        (False, True, True),
        (False, False, True),
        (None, True, False),
        (None, False, True),
    ),
)
def test_get_all_feature_hide_disabled_flags(
    project,
    environment,
    identity,
    environment_value,
    project_value,
    disabled_flag_returned,
):
    # Given
    project.hide_disabled_flags = project_value
    project.save()

    environment.hide_disabled_flags = environment_value
    environment.save()

    # 2 features, both defaulted to True
    feature_one = Feature.objects.create(
        name="Test Feature one",
        project=project,
        default_enabled=True,
    )
    feature_two = Feature.objects.create(
        name="Test Feature two",
        project=project,
        default_enabled=True,
    )
    # with one disabled
    FeatureState.objects.create(
        feature=feature_one,
        environment=environment,
        enabled=False,
        identity=identity,
    )
    # and one enabled overridden feature state
    FeatureState.objects.create(
        feature=feature_two,
        environment=environment,
        enabled=False,
        identity=identity,
    )
    # When
    # we get flags for the identity
    identity_flags = identity.get_all_feature_states()

    # Then
    assert bool(identity_flags) == disabled_flag_returned


def test_identity_get_all_feature_states_gets_latest_committed_version(environment):
    # Given
    identity = Identity.objects.create(identifier="identity", environment=environment)

    feature = Feature.objects.create(
        name="versioned_feature",
        project=environment.project,
        default_enabled=False,
        initial_value="v1",
    )

    now = timezone.now()

    # creating the feature above will have created a feature state with version=1,
    # now we create 2 more versions...
    # one of which is live...
    feature_state_v2 = FeatureState.objects.create(
        feature=feature,
        version=2,
        live_from=now,
        enabled=True,
        environment=environment,
    )
    feature_state_v2.feature_state_value.string_value = "v2"
    feature_state_v2.feature_state_value.save()

    # and one which isn't
    not_live_feature_state = FeatureState.objects.create(
        feature=feature,
        version=None,
        live_from=None,
        enabled=False,
        environment=environment,
    )
    not_live_feature_state.feature_state_value.string_value = "v3"
    not_live_feature_state.feature_state_value.save()

    # When
    identity_feature_states = identity.get_all_feature_states()

    # Then
    identity_feature_state = next(
        filter(lambda fs: fs.feature == feature, identity_feature_states)
    )
    assert identity_feature_state.get_feature_state_value() == "v2"


def test_get_hash_key_with_use_identity_composite_key_for_hashing_enabled(
    identity: Identity,
):
    assert (
        identity.get_hash_key(use_identity_composite_key_for_hashing=True)
        == f"{identity.environment.api_key}_{identity.identifier}"
    )


def test_get_hash_key_with_use_identity_composite_key_for_hashing_disabled(
    identity: Identity,
):
    assert identity.get_hash_key(use_identity_composite_key_for_hashing=False) == str(
        identity.id
    )


def test_identity_get_all_feature_states__returns_identity_override__when_v2_feature_versioning_enabled(
    identity: Identity, environment_v2_versioning: "Environment", feature: Feature
):
    # Given
    identity_override = FeatureState.objects.create(
        environment=environment_v2_versioning, identity=identity, feature=feature
    )

    # When
    all_feature_states = identity.get_all_feature_states()

    # Then
    assert len(all_feature_states) == 1
    assert all_feature_states[0] == identity_override
