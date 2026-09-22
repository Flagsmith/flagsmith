import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from segments.models import Segment
from util.mappers.engine import (
    IDENTITY_OVERRIDES_SEGMENT_KEY,
    IDENTITY_OVERRIDES_SEGMENT_NAME,
    map_environment_to_evaluation_context,
    map_feature_state_to_feature_context,
)


def test_map_environment_to_evaluation_context__environment_default__populates_features(
    identity: Identity,
    feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=feature, environment=identity.environment
    )

    # When
    context, feature_states_by_id = map_environment_to_evaluation_context(
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
            "metadata": {
                "feature_id": feature.pk,
                "feature_state_id": feature_state.pk,
            },
        }
    }
    assert feature_states_by_id == {feature_state.pk: feature_state}


def test_map_environment_to_evaluation_context__transient_identity__omits_stored_traits(
    environment: Environment,
) -> None:
    # Given
    # A transient identity is never saved, so it has no traits to read.
    transient_identity = Identity(identifier="transient", environment=environment)

    # When
    context, _ = map_environment_to_evaluation_context(
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
    context, _ = map_environment_to_evaluation_context(
        environment=identity.environment,
        identity=identity,
        segments=identity.environment.get_segments_from_cache(),
    )

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
    context, _ = map_environment_to_evaluation_context(
        environment=identity.environment,
        identity=identity,
        segments=identity.environment.get_segments_from_cache(),
    )

    # Then
    segment_context = context["segments"][IDENTITY_OVERRIDES_SEGMENT_KEY]
    assert segment_context["name"] == IDENTITY_OVERRIDES_SEGMENT_NAME
    assert segment_context["metadata"] == {"source": "identity_overrides"}
    (override_context,) = segment_context["overrides"]
    # No segment override may outrank an identity override.
    assert override_context["priority"] == float("-inf")
    assert override_context["metadata"]["feature_state_id"] == override.pk
    assert override_context["metadata"]["identity_id"] == identity.pk


def test_map_environment_to_evaluation_context__multivariate_feature__weights_variants_in_id_order(
    identity: Identity,
    multivariate_feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=multivariate_feature, environment=identity.environment
    )

    # When
    context, _ = map_environment_to_evaluation_context(
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
    """The identity key seeds multivariate allocation, so which one is used matters."""
    # Given
    environment = identity.environment
    environment.use_identity_composite_key_for_hashing = (
        use_identity_composite_key_for_hashing
    )
    environment.save()

    # When
    context, _ = map_environment_to_evaluation_context(
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
    """The context key seeds multivariate allocation.

    It has to be the lineage constant (#7913), so that recreating a feature
    state does not move enrolled identities to another variant.
    """
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
