import pytest
from flag_engine.segments.constants import EQUAL

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from evaluation.services import evaluate_identity
from features.constants import CONTROL_VARIANT_KEY
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.value_types import STRING
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from tests.evaluation_helpers import evaluate_feature_state

#: `multivariate_feature`'s initial value, served when nothing is allocated.
CONTROL_VALUE = "control"


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
    assert flag["metadata"]["feature_state"] == identity_override


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


#: How the identity keys below bucket for `MV_HASHING_SALT` under ten equal
#: variants, so each expectation names the decile its hash falls in.
#:
#: Derived from Core API's allocation as it stood before flag-engine took it
#: over — an md5 of "{seed},{identity key}", modulo 9999, over 9998 — and
#: frozen here as plain data. Deliberately not computed with the engine's own
#: hashing, which would move in step with any change and assert nothing.
#:
#: A failure here means enrolled identities would land on a different variant
#: than they do in production. See #7913.
MV_HASHING_SALT = 1
VARIANT_BY_IDENTITY_KEY = {
    "identity-0": "variant-9",
    "identity-1": "variant-9",
    "identity-2": "variant-9",
    "identity-3": "variant-2",
    "identity-4": "variant-1",
    "identity-5": "variant-3",
    "identity-6": "variant-4",
    "identity-7": "variant-1",
    "identity-8": "variant-2",
    "identity-9": "variant-1",
}


def test_evaluate_feature_state__multivariate_feature__buckets_as_before_the_engine(
    environment: Environment,
    project: Project,
) -> None:
    # Given
    # a multivariate feature split into ten equal variants, so that the variant
    # an identity gets names the decile its hash fell in
    feature = Feature.objects.create(
        name="decile_feature",
        project=project,
        type=MULTIVARIATE,
        initial_value="control",
    )
    for index in range(10):
        MultivariateFeatureOption.objects.create(
            feature=feature,
            default_percentage_allocation=10,
            type=STRING,
            string_value=f"variant-{index}-value",
            key=f"variant-{index}",
        )

    feature_state = FeatureState.objects.get(
        environment=environment, feature=feature, identity=None, feature_segment=None
    )
    feature_state.mv_hashing_salt = MV_HASHING_SALT
    feature_state.save()

    # When
    variant_by_identity_key = {
        identity_key: evaluate_feature_state(feature_state, identity_key).variant
        for identity_key in VARIANT_BY_IDENTITY_KEY
    }

    # Then
    assert variant_by_identity_key == VARIANT_BY_IDENTITY_KEY


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


@pytest.mark.parametrize(
    ["identity_key", "expected_variant", "expected_value"],
    (
        pytest.param("identity-4", "variant-1", "variant-1-value", id="first_band"),
        pytest.param("identity-3", "variant-2", "variant-2-value", id="second_band"),
        pytest.param(
            "identity-0",
            CONTROL_VARIANT_KEY,
            CONTROL_VALUE,
            id="unallocated_falls_through",
        ),
    ),
)
def test_evaluate_feature_state__multivariate_feature__allocates_variants_in_order(
    environment: Environment,
    multivariate_feature: Feature,
    identity_key: str,
    expected_variant: str,
    expected_value: str,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        environment=environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )
    feature_state.mv_hashing_salt = 1
    feature_state.save()

    # Two variants taking 20% and 30%, leaving half the range to the control.
    # The fixture gives two of its options the same value, so name them apart.
    for index, (mv_value, allocation) in enumerate(
        zip(
            feature_state.multivariate_feature_state_values.order_by("id"),
            (20, 30, 0),
        )
    ):
        mv_value.percentage_allocation = allocation
        mv_value.save()
        option = mv_value.multivariate_feature_option
        option.key = f"variant-{index + 1}"
        option.string_value = f"variant-{index + 1}-value"
        option.save()

    # When
    evaluated = evaluate_feature_state(feature_state, identity_key)

    # Then
    assert evaluated.variant == expected_variant
    assert evaluated.value == expected_value
