import pytest
from django.db.models import Q
from flag_engine.segments.constants import EQUAL
from pytest_django import DjangoAssertNumQueries
from pytest_lazy_fixtures import lf as lazy_fixture

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from evaluation.mappers import (
    IDENTITY_OVERRIDES_SEGMENT_NAME,
    map_environment_to_evaluation_context,
    map_feature_state_to_feature_context,
)
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule


def test_map_environment_to_evaluation_context__full_environment__returns_expected_context(
    environment: Environment,
    identity: Identity,
    trait: Trait,
    feature: Feature,
    multivariate_feature: Feature,
    identity_matching_segment: Segment,
) -> None:
    # Given
    # a feature overridden by both a segment and the identity
    feature_default = FeatureState.objects.get(feature=feature, environment=environment)
    segment_override = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=identity_matching_segment,
            environment=environment,
            priority=3,
        ),
        enabled=True,
    )
    identity_override = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        identity=identity,
        enabled=True,
    )
    for override, value in (
        (segment_override, "segment override"),
        (identity_override, "identity override"),
    ):
        override.feature_state_value.string_value = value
        override.feature_state_value.save()

    # a multivariate feature left at its environment default
    multivariate_default = FeatureState.objects.get(
        feature=multivariate_feature, environment=environment
    )

    # a segment with a nested rule
    rule = SegmentRule.objects.get(segment=identity_matching_segment)
    nested_rule = SegmentRule.objects.create(rule=rule, type=SegmentRule.ANY_RULE)
    Condition.objects.create(
        rule=nested_rule,
        property="nested",
        operator=EQUAL,
        value="value",
    )

    # When
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        segments=environment.get_segments_from_cache(),
    )

    # Then
    assert context == {
        "environment": {
            "key": environment.api_key,
            "name": "Test Environment",
        },
        "identity": {
            "identifier": "test_identity",
            "key": identity.get_hash_key(
                environment.use_identity_composite_key_for_hashing
            ),
            "traits": {"key1": "value1"},
        },
        "segments": {
            str(identity_matching_segment.pk): {
                "key": str(identity_matching_segment.pk),
                "name": "Matching segment",
                "rules": [
                    {
                        "type": "ALL",
                        "conditions": [
                            {
                                "property": "key1",
                                "operator": "EQUAL",
                                "value": "value1",
                            },
                        ],
                        "rules": [
                            {
                                "type": "ANY",
                                "conditions": [
                                    {
                                        "property": "nested",
                                        "operator": "EQUAL",
                                        "value": "value",
                                    },
                                ],
                                "rules": [],
                            },
                        ],
                    },
                ],
                "overrides": [
                    {
                        "key": str(segment_override.pk),
                        "name": "Test Feature1",
                        "enabled": True,
                        "value": "segment override",
                        "priority": 3,
                        "metadata": {"feature_state": segment_override},
                    },
                ],
                "metadata": {"pk": identity_matching_segment.pk},
            },
            IDENTITY_OVERRIDES_SEGMENT_NAME: {
                "key": IDENTITY_OVERRIDES_SEGMENT_NAME,
                "name": IDENTITY_OVERRIDES_SEGMENT_NAME,
                "rules": [
                    {
                        "type": "ALL",
                        "conditions": [
                            {
                                "property": "$.identity.key",
                                "operator": "IS_SET",
                                "value": "",
                            },
                        ],
                    },
                ],
                "overrides": [
                    {
                        "key": str(identity_override.pk),
                        "name": "Test Feature1",
                        "enabled": True,
                        "value": "identity override",
                        # No segment override may outrank an identity override.
                        "priority": float("-inf"),
                        "metadata": {"feature_state": identity_override},
                    },
                ],
                # No metadata: not a segment a caller can name.
            },
        },
        "features": {
            "Test Feature1": {
                "key": str(feature_default.pk),
                "name": "Test Feature1",
                "enabled": False,
                "value": None,
                "metadata": {"feature_state": feature_default},
            },
            "feature": {
                "key": str(multivariate_default.pk),
                "name": "feature",
                "enabled": False,
                "value": "control",
                # Core API allocates percentages in id order; the engine
                # allocates in `priority` order, so priority follows id.
                "variants": [
                    {
                        "value": "multivariate option for 30% of users.",
                        "weight": 30,
                        "priority": 0,
                    },
                    {
                        "value": "multivariate option for 30% of users.",
                        "weight": 30,
                        "priority": 1,
                    },
                    {
                        "value": "multivariate option for 40% of users.",
                        "weight": 40,
                        "priority": 2,
                    },
                ],
                "metadata": {"feature_state": multivariate_default},
            },
        },
    }


@pytest.mark.parametrize(
    ["traits", "expected_traits"],
    (
        pytest.param(None, {}, id="no_traits"),
        pytest.param(
            [Trait(trait_key="request-trait", string_value="request value")],
            {"request-trait": "request value"},
            id="explicit_traits",
        ),
    ),
)
def test_map_environment_to_evaluation_context__transient_identity__returns_explicit_traits_only(
    environment: Environment,
    traits: list[Trait] | None,
    expected_traits: dict[str, str],
) -> None:
    # Given
    # A transient identity is never saved, so it has no stored traits, and
    # reading them from an unsaved instance would raise.
    transient_identity = Identity(identifier="transient", environment=environment)

    # When
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=transient_identity,
        traits=traits,
    )

    # Then
    assert context["identity"] == {
        "identifier": "transient",
        "key": transient_identity.get_hash_key(
            environment.use_identity_composite_key_for_hashing
        ),
        "traits": expected_traits,
    }


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


@pytest.fixture()
def explicit_traits(identity: Identity, trait_key: str) -> list[Trait]:
    return [Trait(identity=identity, trait_key=trait_key, string_value="explicit")]


@pytest.mark.parametrize(
    ["traits", "expected_trait_value"],
    (
        pytest.param(
            lazy_fixture("explicit_traits"),
            "explicit",
            id="explicit_traits_take_precedence",
        ),
        pytest.param(
            None,
            lazy_fixture("trait_value"),
            id="no_explicit_traits_reads_stored",
        ),
    ),
)
def test_map_environment_to_evaluation_context__traits__returns_expected_traits(
    environment: Environment,
    identity: Identity,
    trait: Trait,
    traits: list[Trait] | None,
    expected_trait_value: str,
) -> None:
    # Given / When
    context = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        traits=traits,
    )

    # Then
    identity_context = context["identity"]
    assert identity_context
    assert identity_context["traits"] == {trait.trait_key: expected_trait_value}


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


@pytest.mark.parametrize("segment_count", [1, 3])
def test_map_environment_to_evaluation_context__inputs_not_prefetched__queries_do_not_scale(
    segment_count: int,
    environment: Environment,
    project: Project,
    identity: Identity,
    trait: Trait,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    for i in range(segment_count):
        segment = Segment.objects.create(name=f"segment_{i}", project=project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(
            rule=SegmentRule.objects.create(rule=rule, type=SegmentRule.ANY_RULE),
            property=trait.trait_key,
            operator=EQUAL,
            value=trait.trait_value,
        )
    segments = Segment.objects.filter(project=project)
    identity = Identity.objects.get(pk=identity.pk)

    # When / Then
    with django_assert_num_queries(9):
        map_environment_to_evaluation_context(
            environment=environment,
            identity=identity,
            segments=segments,
        )


def test_map_environment_to_evaluation_context__additional_filters__narrows_features(
    identity: Identity,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    other_feature = Feature.objects.create(name="other_feature", project=project)

    # When
    context = map_environment_to_evaluation_context(
        environment=identity.environment,
        identity=identity,
        additional_filters=Q(feature__name=other_feature.name),
    )

    # Then
    assert set(context["features"]) == {other_feature.name}
