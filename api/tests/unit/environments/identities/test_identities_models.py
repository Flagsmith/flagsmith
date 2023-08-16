from django.utils import timezone

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState


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


def test_get_all_feature_states_where_feature_segment_has_more_than_one_feature_state(
    feature: Feature,
    environment: Environment,
    identity: Identity,
    identity_matching_segment: Identity,
):
    """
    Test to verify what happens in the case that the data model is somehow abused
    and we end up with more than one feature state for a single feature segment.

    TODO: find out _how_ the data model is being abused and we are ending up with
     these duplicates.
    """

    # Given
    # 2 segment overrides for the same feature segment
    feature_segment = FeatureSegment.objects.create(
        environment=environment, segment=identity_matching_segment, feature=feature
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        version=1,
    )
    feature_state_2 = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        version=2,
    )
    # update the feature state to get around the BEFORE_CREATE validation...
    feature_state_2.version = 1
    feature_state_2.save()

    # When
    results = []
    num_iterations = 10
    for _ in range(num_iterations):
        results.extend(identity.get_all_feature_states())

    # Then
    assert len(results) == num_iterations

    unique_feature_states = set(results)
    assert len(unique_feature_states) == 1
    assert unique_feature_states.pop() == feature_state_2
