from features.evaluation import evaluate_feature_state as evaluate_flag
from features.models import FeatureState
from integrations.webhook.serializers import (
    IntegrationFeatureStateSerializer,
    SegmentSerializer,
)


def test_integration_feature_state_serializer__multivariate_feature__returns_correct_weight(  # type: ignore[no-untyped-def]
    identity, multivariate_feature, mocker
):
    # Given
    mv_option = multivariate_feature.multivariate_options.first()
    feature_state = FeatureState.objects.filter(feature=multivariate_feature).first()
    # Bucket the identity into the first option, whatever its weight.
    mocker.patch(
        "flag_engine.segments.evaluator.get_hashed_percentage_for_object_ids",
        return_value=0.0,
    )
    feature_state.flag_result = evaluate_flag(feature_state, identity.get_hash_key())

    # When
    serializer = IntegrationFeatureStateSerializer(
        feature_state, context={"identity": identity}
    )
    data = serializer.data

    # Then
    assert data["percentage_allocation"] == mv_option.default_percentage_allocation
    assert data["feature_state_value"] == mv_option.value


def test_segment_serializer__identity_matching_segment__returns_member_true(  # type: ignore[no-untyped-def]
    identity, trait, identity_matching_segment
):
    # Given
    serializer = SegmentSerializer(
        identity_matching_segment, context={"identity": identity}
    )
    # When
    data = serializer.data
    # Then
    assert data["member"] is True
    assert data["id"] == identity_matching_segment.id
