import pytest
from flag_engine.segments.constants import EQUAL
from flag_engine.utils.hashing import get_hashed_percentage_for_object_ids

from environments.identities.evaluation import (
    build_identity_evaluation_context,
    evaluate_identity,
)
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from util.mappers.engine import (
    IDENTITY_OVERRIDES_SEGMENT_KEY,
    IDENTITY_OVERRIDES_SEGMENT_NAME,
)


def test_build_identity_evaluation_context__environment_default__populates_features(
    identity: Identity,
    feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=feature, environment=identity.environment
    )

    # When
    context, feature_states_by_id = build_identity_evaluation_context(identity)

    # Then
    assert context["features"] == {
        feature.name: {
            "key": str(feature_state.pk),
            "name": feature.name,
            "enabled": feature_state.enabled,
            "value": feature_state.get_feature_state_value(),
            "metadata": {
                "feature_id": feature.pk,
                "feature_state_id": feature_state.pk,
            },
        }
    }
    assert feature_states_by_id == {feature_state.pk: feature_state}


def test_build_identity_evaluation_context__transient_identity__omits_stored_traits(
    environment: Environment,
) -> None:
    # Given
    # A transient identity is never saved, so it has no traits to read.
    transient_identity = Identity(identifier="transient", environment=environment)

    # When
    context, _ = build_identity_evaluation_context(transient_identity)

    # Then
    assert context["identity"] == {
        "identifier": "transient",
        "key": transient_identity.get_hash_key(
            environment.use_identity_composite_key_for_hashing
        ),
        "traits": {},
    }


def test_build_identity_evaluation_context__segment_override__carries_segment_id(
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
    context, _ = build_identity_evaluation_context(identity)

    # Then
    segment_context = context["segments"][str(identity_matching_segment.pk)]
    assert segment_context["metadata"] == {
        "source": "segment",
        "pk": identity_matching_segment.pk,
    }
    (override_context,) = segment_context["overrides"]
    assert override_context["priority"] == 3
    assert override_context["metadata"] == {
        "feature_id": feature.pk,
        "feature_state_id": override.pk,
        "segment_id": identity_matching_segment.pk,
    }


def test_build_identity_evaluation_context__identity_override__returns_synthetic_segment(
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
    context, _ = build_identity_evaluation_context(identity)

    # Then
    segment_context = context["segments"][IDENTITY_OVERRIDES_SEGMENT_KEY]
    assert segment_context["name"] == IDENTITY_OVERRIDES_SEGMENT_NAME
    assert segment_context["metadata"] == {"source": "identity_overrides"}
    (override_context,) = segment_context["overrides"]
    # No segment override may outrank an identity override.
    assert override_context["priority"] == float("-inf")
    assert override_context["metadata"]["feature_state_id"] == override.pk
    assert override_context["metadata"]["identity_id"] == identity.pk


def test_evaluate_identity__identity_and_segment_override__identity_override_wins(
    identity: Identity,
    feature: Feature,
    identity_matching_segment: Segment,
) -> None:
    # Given
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=identity_matching_segment,
        environment=identity.environment,
        # A priority high enough to beat every other segment override, but not
        # an identity override.
        priority=0,
    )
    segment_override = FeatureState.objects.create(
        feature=feature,
        environment=identity.environment,
        feature_segment=feature_segment,
        enabled=True,
    )
    segment_override.feature_state_value.string_value = "segment"
    segment_override.feature_state_value.save()

    identity_override = FeatureState.objects.create(
        identity=identity,
        feature=feature,
        environment=identity.environment,
        enabled=True,
    )
    identity_override.feature_state_value.string_value = "identity"
    identity_override.feature_state_value.save()

    # When
    result, _ = evaluate_identity(identity)

    # Then
    flag = result["flags"][feature.name]
    assert flag["value"] == "identity"
    assert flag["metadata"]["feature_state_id"] == identity_override.pk


def test_evaluate_identity__segment_overrides__lowest_priority_wins(
    identity: Identity,
    feature: Feature,
    identity_matching_segment: Segment,
    project: Project,
    trait: Trait,
) -> None:
    # Given
    # A second segment the identity also matches, overriding the same feature.
    other_segment = Segment.objects.create(name="Everyone", project=project)
    Condition.objects.create(
        rule=SegmentRule.objects.create(
            segment=other_segment, type=SegmentRule.ALL_RULE
        ),
        property=trait.trait_key,
        operator=EQUAL,
        value=trait.trait_value,
    )

    for segment, priority, value in (
        (identity_matching_segment, 1, "winner"),
        (other_segment, 2, "loser"),
    ):
        feature_segment = FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=identity.environment,
            priority=priority,
        )
        override = FeatureState.objects.create(
            feature=feature,
            environment=identity.environment,
            feature_segment=feature_segment,
        )
        override.feature_state_value.string_value = value
        override.feature_state_value.save()

    # When
    result, _ = evaluate_identity(identity)

    # Then
    assert result["flags"][feature.name]["value"] == "winner"


@pytest.mark.parametrize("mv_hashing_salt", [None, 12345])
def test_evaluate_identity__multivariate_feature__matches_legacy_bucketing(
    identity: Identity,
    multivariate_feature: Feature,
    mv_hashing_salt: int | None,
) -> None:
    """The engine must bucket an identity exactly as Core API used to.

    Core API seeds allocation on `mv_hashing_seed`, a lineage constant that
    survives a feature state being recreated (#7913). Seeding on anything else
    — the feature state id, say — would silently move enrolled identities to a
    different variant.
    """
    # Given
    feature_state = FeatureState.objects.get(
        feature=multivariate_feature, environment=identity.environment
    )
    feature_state.mv_hashing_salt = mv_hashing_salt
    feature_state.save()

    hash_key = identity.get_hash_key(
        identity.environment.use_identity_composite_key_for_hashing
    )
    expected_value = feature_state.get_feature_state_value_by_hash_key(hash_key)

    # When
    result, _ = evaluate_identity(identity)

    # Then
    assert result["flags"][multivariate_feature.name]["value"] == expected_value
    # And the seed the engine used is the lineage constant, not the row id.
    assert get_hashed_percentage_for_object_ids(
        [str(feature_state.mv_hashing_seed), hash_key]
    ) == get_hashed_percentage_for_object_ids([feature_state.mv_hashing_seed, hash_key])


def test_evaluate_identity__multivariate_feature__returns_variant_key(
    identity: Identity,
    multivariate_feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=multivariate_feature, environment=identity.environment
    )
    for index, mv_value in enumerate(
        MultivariateFeatureStateValue.objects.filter(
            feature_state=feature_state
        ).order_by("id")
    ):
        mv_value.multivariate_feature_option.key = f"variant-{index}"
        mv_value.multivariate_feature_option.save()

    # When
    result, _ = evaluate_identity(identity)

    # Then
    flag = result["flags"][multivariate_feature.name]
    # Either a named variant or the control bucket — never a silent `None`,
    # which is what an unkeyed variant context would produce.
    assert flag["variant"] in {"control", "variant-0", "variant-1", "variant-2"}


def test_evaluate_identity__multivariate_feature__weights_variants_in_id_order(
    identity: Identity,
    multivariate_feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=multivariate_feature, environment=identity.environment
    )

    # When
    context, _ = build_identity_evaluation_context(identity)

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
