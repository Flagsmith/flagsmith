import pytest
from flag_engine.segments.constants import EQUAL
from pytest_lazy_fixtures import lf as lazy_fixture

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from evaluation.mappers import (
    IDENTITY_OVERRIDES_SEGMENT_KEY,
    IDENTITY_OVERRIDES_SEGMENT_NAME,
    map_environment_to_evaluation_context,
    map_feature_state_to_feature_context,
)
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from segments.models import Condition, Segment, SegmentRule


def test_map_environment_to_evaluation_context__environment_default__populates_features(
    identity: Identity,
    feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=feature, environment=identity.environment
    )

    # When
    context = map_environment_to_evaluation_context(
        environment=identity.environment,
        identity=identity,
        segments=identity.environment.get_segments_from_cache(),
    )

    # Then
    assert context["features"] == {
        feature.name: {
            "key": str(feature_state.pk),
            "name": feature.name,
            "enabled": feature_state.enabled,
            "value": feature_state.get_feature_state_value(),
            "metadata": {"feature_state": feature_state},
        }
    }


def test_map_environment_to_evaluation_context__transient_identity__omits_stored_traits(
    environment: Environment,
) -> None:
    # Given
    # A transient identity is never saved, so it has no traits to read.
    transient_identity = Identity(identifier="transient", environment=environment)

    # When
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=transient_identity,
    )

    # Then
    assert context["identity"] == {
        "identifier": "transient",
        "key": transient_identity.get_hash_key(
            environment.use_identity_composite_key_for_hashing
        ),
        "traits": {},
    }


def test_map_environment_to_evaluation_context__segment_override__carries_segment_id(
    identity: Identity,
    feature: Feature,
    identity_matching_segment: Segment,
) -> None:
    # Given
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=identity_matching_segment,
        environment=identity.environment,
        priority=3,
    )
    override = FeatureState.objects.create(
        feature=feature,
        environment=identity.environment,
        feature_segment=feature_segment,
        enabled=True,
    )

    # When
    context = map_environment_to_evaluation_context(
        environment=identity.environment,
        identity=identity,
        segments=identity.environment.get_segments_from_cache(),
    )

    # Then
    segment_context = context["segments"][str(identity_matching_segment.pk)]
    assert segment_context["metadata"] == {"pk": identity_matching_segment.pk}
    (override_context,) = segment_context["overrides"]
    assert override_context["priority"] == 3
    assert override_context["metadata"] == {"feature_state": override}


def test_map_environment_to_evaluation_context__identity_override__returns_synthetic_segment(
    identity: Identity,
    feature: Feature,
) -> None:
    # Given
    override = FeatureState.objects.create(
        identity=identity,
        feature=feature,
        environment=identity.environment,
        enabled=True,
    )

    # When
    context = map_environment_to_evaluation_context(
        environment=identity.environment,
        identity=identity,
        segments=identity.environment.get_segments_from_cache(),
    )

    # Then
    segment_context = context["segments"][IDENTITY_OVERRIDES_SEGMENT_KEY]
    assert segment_context["name"] == IDENTITY_OVERRIDES_SEGMENT_NAME
    assert "metadata" not in segment_context
    (override_context,) = segment_context["overrides"]
    # No segment override may outrank an identity override.
    assert override_context["priority"] == float("-inf")
    assert override_context["metadata"] == {"feature_state": override}


def test_map_environment_to_evaluation_context__multivariate_feature__weights_variants_in_id_order(
    identity: Identity,
    multivariate_feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=multivariate_feature, environment=identity.environment
    )

    # When
    context = map_environment_to_evaluation_context(
        environment=identity.environment,
        identity=identity,
        segments=identity.environment.get_segments_from_cache(),
    )

    # Then
    # Core API allocates percentages in id order; the engine allocates in
    # `priority` order, so the two only agree if priority follows id.
    mv_values = MultivariateFeatureStateValue.objects.filter(
        feature_state=feature_state
    ).order_by("id")
    assert context["features"][multivariate_feature.name]["variants"] == [
        {
            "value": mv_value.multivariate_feature_option.value,
            "weight": mv_value.percentage_allocation,
            "priority": index,
        }
        for index, mv_value in enumerate(mv_values)
    ]


@pytest.mark.parametrize(
    "use_identity_composite_key_for_hashing",
    [True, False],
)
def test_map_environment_to_evaluation_context__hashing_setting__sets_matching_identity_key(
    identity: Identity,
    use_identity_composite_key_for_hashing: bool,
) -> None:
    # Given
    environment = identity.environment
    environment.use_identity_composite_key_for_hashing = (
        use_identity_composite_key_for_hashing
    )
    environment.save()

    # When
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
    )

    # Then
    identity_context = context["identity"]
    assert identity_context
    assert identity_context["key"] == (
        identity.composite_key
        if use_identity_composite_key_for_hashing
        else str(identity.pk)
    )


@pytest.mark.parametrize(
    ["mv_hashing_salt", "expected_key"],
    [
        pytest.param(None, "id", id="no_salt"),
        pytest.param(999, "999", id="salt_set"),
    ],
)
def test_map_feature_state_to_feature_context__multivariate_feature__keys_on_hashing_seed(
    environment: Environment,
    multivariate_feature: Feature,
    mv_hashing_salt: int | None,
    expected_key: str,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )
    feature_state.mv_hashing_salt = mv_hashing_salt

    # When
    feature_context = map_feature_state_to_feature_context(feature_state)

    # Then
    assert feature_context["key"] == (
        str(feature_state.id) if expected_key == "id" else expected_key
    )


def test_map_environment_to_evaluation_context__no_identity__returns_environment_only(
    environment: Environment,
) -> None:
    # Given / When
    context = map_environment_to_evaluation_context(environment=environment)

    # Then
    assert context == {
        "environment": {
            "key": environment.api_key,
            "name": environment.name,
        },
        "features": {},
    }


def test_map_environment_to_evaluation_context__with_identity__returns_identity_context(
    environment: Environment,
    identity: Identity,
) -> None:
    # Given / When
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
    )

    # Then
    assert context == {
        "environment": {
            "key": environment.api_key,
            "name": environment.name,
        },
        "identity": {
            "identifier": identity.identifier,
            "key": identity.get_hash_key(
                environment.use_identity_composite_key_for_hashing
            ),
            "traits": {},
        },
        "features": {},
    }


TRAIT_KEY = "trait-key"


@pytest.fixture()
def stored_trait(identity: Identity) -> Trait:
    return Trait.objects.create(
        identity=identity, trait_key=TRAIT_KEY, string_value="stored"
    )


@pytest.fixture()
def explicit_traits(identity: Identity) -> list[Trait]:
    return [Trait(identity=identity, trait_key=TRAIT_KEY, string_value="explicit")]


@pytest.mark.parametrize(
    ["traits", "expected_traits"],
    (
        pytest.param(
            lazy_fixture("explicit_traits"),
            {TRAIT_KEY: "explicit"},
            id="explicit_traits_take_precedence",
        ),
        pytest.param(
            None,
            {TRAIT_KEY: "stored"},
            id="no_explicit_traits_reads_stored",
        ),
    ),
)
def test_map_environment_to_evaluation_context__traits__returns_expected_traits(
    environment: Environment,
    identity: Identity,
    stored_trait: Trait,
    traits: list[Trait] | None,
    expected_traits: dict[str, str],
) -> None:
    # Given / When
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        traits=traits,
    )

    # Then
    assert context == {
        "environment": {
            "key": environment.api_key,
            "name": environment.name,
        },
        "identity": {
            "identifier": identity.identifier,
            "key": identity.get_hash_key(
                environment.use_identity_composite_key_for_hashing
            ),
            "traits": expected_traits,
        },
        "features": {},
    }


def test_map_environment_to_evaluation_context__with_segments__returns_segment_contexts(
    environment: Environment,
    identity_matching_segment: Segment,
) -> None:
    # Given
    rule = SegmentRule.objects.get(segment=identity_matching_segment)
    condition = Condition.objects.get(rule=rule)
    nested_rule = SegmentRule.objects.create(rule=rule, type=SegmentRule.ANY_RULE)
    nested_condition = Condition.objects.create(
        rule=nested_rule,
        property="nested",
        operator=EQUAL,
        value="value",
    )

    # When
    context = map_environment_to_evaluation_context(
        environment=environment,
        segments=[identity_matching_segment],
    )

    # Then
    assert context == {
        "environment": {
            "key": environment.api_key,
            "name": environment.name,
        },
        "segments": {
            str(identity_matching_segment.pk): {
                "key": str(identity_matching_segment.pk),
                "name": identity_matching_segment.name,
                "rules": [
                    {
                        "type": "ALL",
                        "conditions": [
                            {
                                "property": condition.property,
                                "operator": condition.operator,
                                "value": condition.value,
                            },
                        ],
                        "rules": [
                            {
                                "type": "ANY",
                                "conditions": [
                                    {
                                        "property": nested_condition.property,
                                        "operator": nested_condition.operator,
                                        "value": nested_condition.value,
                                    },
                                ],
                                "rules": [],
                            },
                        ],
                    },
                ],
                "metadata": {"pk": identity_matching_segment.pk},
            },
        },
        "features": {},
    }


def test_map_environment_to_evaluation_context__system_traits__merged_with_system_winning(
    identity: Identity,
    trait: Trait,
) -> None:
    # Given
    identity.system_traits = {trait.trait_key: "system value"}
    identity.save()

    # When
    context = map_environment_to_evaluation_context(
        environment=identity.environment,
        identity=identity,
    )

    # Then
    identity_context = context["identity"]
    assert identity_context
    # System-owned traits are not user data, so they win a key clash.
    assert identity_context["traits"] == {trait.trait_key: "system value"}


def test_map_feature_state_to_feature_context__keyed_options__returns_variant_keys(
    environment: Environment,
    multivariate_feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )
    mv_fs_values = list(
        MultivariateFeatureStateValue.objects.filter(
            feature_state=feature_state
        ).order_by("id")
    )
    for index, mv_fs_value in enumerate(mv_fs_values):
        mv_fs_value.multivariate_feature_option.key = f"variant-{index}"
        mv_fs_value.multivariate_feature_option.save()

    # When
    feature_context = map_feature_state_to_feature_context(
        feature_state, mv_fs_values=mv_fs_values
    )

    # Then
    # Without a key the engine reports every result as the control bucket.
    assert [variant["key"] for variant in feature_context["variants"]] == [
        f"variant-{index}" for index in range(len(mv_fs_values))
    ]
