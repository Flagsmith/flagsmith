import pytest
from flag_engine.segments.constants import EQUAL, IN, IS_SET
from pytest_lazy_fixtures import lf as lazy_fixture

from edge_api.identities.models import EdgeIdentity
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from evaluation.services import (
    evaluate_identity,
    get_edge_identity_feature_states,
    get_edge_identity_override_value,
    get_edge_identity_segments,
)
from features.constants import CONTROL_VARIANT_KEY
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.value_types import INTEGER, STRING
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from util.engine_models.features.models import (
    FeatureModel,
    FeatureStateModel,
    MultivariateFeatureOptionModel,
    MultivariateFeatureStateValueList,
    MultivariateFeatureStateValueModel,
)
from util.engine_models.identities.models import IdentityFeaturesList, IdentityModel
from util.engine_models.identities.traits.models import TraitModel
from util.mappers import map_identity_to_identity_document


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
    evaluated_feature_states = get_edge_identity_feature_states(edge_identity)

    # Then
    (evaluated_feature_state,) = [
        evaluated_feature_state
        for evaluated_feature_state in evaluated_feature_states
        if evaluated_feature_state.evaluation_result["name"] == feature.name
    ]
    assert evaluated_feature_state.evaluation_result["value"] == "identity"
    assert evaluated_feature_state.feature_state == (edge_identity.feature_overrides[0])


def test_get_edge_identity_segments__matching_segment_exists__returns_matching_only(
    project: Project,
    environment: Environment,
    identity: Identity,
    identity_matching_segment: Segment,
) -> None:
    # Given - two segments (one that matches the identity and one that does not)
    Segment.objects.create(name="Non matching segment", project=project)

    edge_identity = EdgeIdentity.from_identity_document(
        map_identity_to_identity_document(identity)
    )

    # When
    segments = get_edge_identity_segments(edge_identity)

    # Then
    assert segments == [identity_matching_segment]


def test_get_edge_identity_segments__segment_with_feature_overrides__returns_matching_only(
    project: Project,
    environment: Environment,
    feature: Feature,
    identity: Identity,
    identity_matching_segment: Segment,
) -> None:
    # Given - a segment with two feature overrides:
    # one simple override and one with multivariate values
    simple_feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=identity_matching_segment,
        environment=environment,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=simple_feature_segment,
        enabled=True,
    )

    mv_feature = Feature.objects.create(
        name="mv_feature",
        project=project,
        type="MULTIVARIATE",
    )
    mv_option = MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=30,
        type="unicode",
        string_value="variant_a",
    )
    mv_feature_segment = FeatureSegment.objects.create(
        feature=mv_feature,
        segment=identity_matching_segment,
        environment=environment,
    )
    mv_feature_state = FeatureState.objects.create(
        feature=mv_feature,
        environment=environment,
        feature_segment=mv_feature_segment,
        enabled=True,
    )
    MultivariateFeatureStateValue.objects.create(
        feature_state=mv_feature_state,
        multivariate_feature_option=mv_option,
        percentage_allocation=30,
    )

    edge_identity = EdgeIdentity.from_identity_document(
        map_identity_to_identity_document(identity)
    )

    # When
    segments = get_edge_identity_segments(edge_identity)

    # Then
    assert segments == [identity_matching_segment]


def test_get_edge_identity_segments__system_trait_backed_segment__returns_matching_only(
    project: Project,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given - two IS_SET segments: one keyed to a system trait the identity
    # carries, one keyed to a system trait it does not
    member_segment = Segment.objects.create(name="Cohort members", project=project)
    rule = SegmentRule.objects.create(segment=member_segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(rule=rule, operator=IS_SET, property="flagsmith_cohort_a")
    other_segment = Segment.objects.create(name="Other cohort", project=project)
    other_rule = SegmentRule.objects.create(
        segment=other_segment, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        rule=other_rule, operator=IS_SET, property="flagsmith_cohort_b"
    )

    identity_document = map_identity_to_identity_document(identity)
    identity_document["system_traits"] = {"flagsmith_cohort_a": True}
    edge_identity = EdgeIdentity.from_identity_document(identity_document)

    # When
    segments = get_edge_identity_segments(edge_identity)

    # Then
    assert segments == [member_segment]


def test_get_edge_identity_segments__in_operator_with_integer_traits__returns_matching_only(
    project: Project,
    environment: Environment,
) -> None:
    """
    Specific test to cover https://github.com/Flagsmith/flagsmith/issues/2602
    """
    # Given
    trait_key = "trait_key"

    segment = Segment.objects.create(name="Test Segment", project=project)
    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    child_rule = SegmentRule.objects.create(rule=parent_rule, type=SegmentRule.ANY_RULE)
    Condition.objects.create(
        property=trait_key, operator=IN, value="1,2,3,4", rule=child_rule
    )

    identity = Identity.objects.create(environment=environment, identifier="identifier")
    Trait.objects.create(
        trait_key=trait_key, integer_value=1, value_type=INTEGER, identity=identity
    )

    edge_identity = EdgeIdentity.from_identity_document(
        map_identity_to_identity_document(identity)
    )

    # When
    segments = get_edge_identity_segments(edge_identity)

    # Then
    assert segments == [segment]


@pytest.mark.parametrize(
    "allocations",
    [
        pytest.param([], id="no_variants"),
        pytest.param([100], id="pinned_variant"),
        pytest.param([30, 40], id="split"),
    ],
)
def test_get_edge_identity_override_value__override__returns_served_value(
    allocations: list[float],
    environment: Environment,
    multivariate_feature: Feature,
) -> None:
    # Given
    options = multivariate_feature.multivariate_options.order_by("id")
    override = FeatureStateModel(
        feature=FeatureModel(
            id=multivariate_feature.id,
            name=multivariate_feature.name,
            type=multivariate_feature.type,
        ),
        enabled=True,
        feature_state_value="control",
        multivariate_feature_state_values=MultivariateFeatureStateValueList(
            [
                MultivariateFeatureStateValueModel(
                    id=id_,
                    percentage_allocation=allocation,
                    multivariate_feature_option=MultivariateFeatureOptionModel(
                        id=option.id, value=option.value
                    ),
                )
                for id_, (option, allocation) in enumerate(
                    zip(options, allocations), start=1
                )
            ]
        ),
    )
    edge_identity = EdgeIdentity(
        IdentityModel(
            identifier="identity",
            environment_api_key=environment.api_key,
            identity_features=IdentityFeaturesList([override]),
        )
    )
    (served,) = [
        evaluated_feature_state
        for evaluated_feature_state in get_edge_identity_feature_states(edge_identity)
        if evaluated_feature_state.evaluation_result["name"]
        == multivariate_feature.name
    ]

    # When
    value = get_edge_identity_override_value(
        edge_identity, override, environment=environment
    )

    # Then
    assert value == served.evaluation_result["value"]
