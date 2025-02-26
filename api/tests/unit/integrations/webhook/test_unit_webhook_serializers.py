from features.models import FeatureState
from integrations.webhook.serializers import (
    IntegrationFeatureStateSerializer,
    SegmentSerializer,
)


def test_integration_feature_state_serializer_environment_weight_is_correct(  # type: ignore[no-untyped-def]
    identity, multivariate_feature, mocker
):
    # Given
    mv_option = multivariate_feature.multivariate_options.first()
    mocker.patch.object(
        FeatureState, "get_multivariate_feature_state_value", return_value=mv_option
    )
    feature_state = FeatureState.objects.filter(feature=multivariate_feature).first()

    # When
    serializer = IntegrationFeatureStateSerializer(
        feature_state, context={"identity": identity}
    )
    data = serializer.data

    # Then
    assert data["percentage_allocation"] == mv_option.default_percentage_allocation
    assert data["feature_state_value"] == mv_option.value


def test_segment_serializer_member_is_correct(  # type: ignore[no-untyped-def]
    identity, trait, identity_matching_segment
):
    # When
    serializer = SegmentSerializer(
        identity_matching_segment, context={"identity": identity}
    )
    # Then
    assert serializer.data["member"] is True
    assert serializer.data["id"] == identity_matching_segment.id
