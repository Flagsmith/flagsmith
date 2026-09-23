import pytest
from flag_engine.segments.constants import EQUAL
from pytest_lazy_fixtures import lf as lazy_fixture

from edge_api.identities.models import EdgeIdentity
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from evaluation.services import (
    evaluate_identity,
    get_edge_identity_feature_states,
)
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
from util.engine_models.features.models import FeatureModel, FeatureStateModel
from util.engine_models.identities.models import IdentityFeaturesList, IdentityModel
from util.engine_models.identities.traits.models import TraitModel


@pytest.fixture()
def control_value() -> str:
    return "control"


@pytest.fixture()
def mv_hashing_salt() -> int:
    return 1


@pytest.fixture()
def hashing_environment_api_key() -> str:
    return "test-environment-key"


@pytest.fixture()
def hashing_environment(
    environment: Environment,
    hashing_environment_api_key: str,
) -> Environment:
    """An environment whose identities bucket predictably."""
    environment.api_key = hashing_environment_api_key
    environment.use_identity_composite_key_for_hashing = True
    environment.save()
    return environment


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


def test_evaluate_identity__multivariate_feature__buckets_as_before_the_engine(
    hashing_environment: Environment,
    mv_hashing_salt: int,
    project: Project,
) -> None:
    """The expectations are derived from Core API's allocation as it stood before flag-engine took over."""
    # Given
    # ten equal variants, so the variant an identity gets names the decile its
    # hash fell in
    expected_variant_by_identifier = {
        "identity-0": "variant-3",
        "identity-1": "variant-0",
        "identity-2": "variant-2",
        "identity-3": "variant-5",
        "identity-4": "variant-8",
        "identity-5": "variant-5",
        "identity-6": "variant-1",
        "identity-7": "variant-2",
        "identity-8": "variant-2",
        "identity-9": "variant-1",
    }
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
        environment=hashing_environment,
        feature=feature,
        identity=None,
        feature_segment=None,
    )
    feature_state.mv_hashing_salt = mv_hashing_salt
    feature_state.save()

    # When
    variant_by_identifier = {
        identifier: evaluate_identity(
            Identity.objects.create(
                identifier=identifier, environment=hashing_environment
            )
        ).result["flags"][feature.name]["variant"]
        for identifier in expected_variant_by_identifier
    }

    # Then
    assert variant_by_identifier == expected_variant_by_identifier


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
    # Either a named variant or the control bucket
    assert flag["variant"] in {"control", "variant-0", "variant-1", "variant-2"}


@pytest.mark.parametrize(
    ["identifier", "expected_variant", "expected_value"],
    (
        pytest.param("identity-1", "variant-1", "variant-1-value", id="first_band"),
        pytest.param("identity-2", "variant-2", "variant-2-value", id="second_band"),
        pytest.param(
            "identity-4",
            CONTROL_VARIANT_KEY,
            lazy_fixture("control_value"),
            id="unallocated_falls_through",
        ),
    ),
)
def test_evaluate_identity__multivariate_feature__allocates_variants_in_order(
    hashing_environment: Environment,
    mv_hashing_salt: int,
    multivariate_feature: Feature,
    identifier: str,
    expected_variant: str,
    expected_value: str,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        environment=hashing_environment,
        feature=multivariate_feature,
        identity=None,
        feature_segment=None,
    )
    feature_state.mv_hashing_salt = mv_hashing_salt
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

    identity = Identity.objects.create(
        identifier=identifier, environment=hashing_environment
    )

    # When
    flag = evaluate_identity(identity).result["flags"][multivariate_feature.name]

    # Then
    assert flag["variant"] == expected_variant
    assert flag["value"] == expected_value


def test_get_edge_identity_feature_states__segment_and_identity_override__identity_override_wins(
    environment: Environment,
    feature: Feature,
    identity_matching_segment: Segment,
    trait: Trait,
) -> None:
    # Given
    # a segment override the identity matches
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=identity_matching_segment,
        environment=environment,
        priority=0,
    )
    segment_override = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        enabled=True,
    )
    segment_override.feature_state_value.string_value = "segment"
    segment_override.feature_state_value.save()

    # and an identity override, stored against the identity in DynamoDB
    edge_identity = EdgeIdentity(
        IdentityModel(
            identifier="identity",
            environment_api_key=environment.api_key,
            identity_traits=[
                TraitModel(trait_key=trait.trait_key, trait_value=trait.trait_value)
            ],
            identity_features=IdentityFeaturesList(
                [
                    FeatureStateModel(
                        django_id=1,
                        feature=FeatureModel(
                            id=feature.id, name=feature.name, type=feature.type
                        ),
                        enabled=True,
                        feature_state_value="identity",
                    )
                ]
            ),
        )
    )

    # When
    feature_states = get_edge_identity_feature_states(edge_identity)

    # Then
    (feature_state,) = [
        feature_state
        for feature_state in feature_states
        if feature_state.feature.name == feature.name
    ]
    assert feature_state.feature_state_value == "identity"
