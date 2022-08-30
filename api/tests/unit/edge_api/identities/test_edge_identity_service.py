from edge_api.identities.edge_identity_service import (
    get_all_feature_states_for_edge_identity,
)
from features.models import FeatureSegment, FeatureState, FeatureStateValue
from segments.models import Segment


def test_get_all_feature_states_for_edge_identity_uses_segment_priorities(
    environment, project, segment, feature, mocker
):
    # Given
    another_segment = Segment.objects.create(name="another_segment", project=project)

    dynamo_wrapper_mock = mocker.patch(
        "environments.identities.models.Identity.dynamo_wrapper",
    )
    dynamo_wrapper_mock.get_segment_ids.return_value = [segment.id, another_segment.id]

    feature_segment_p1 = FeatureSegment.objects.create(
        segment=segment, feature=feature, environment=environment, priority=1
    )
    feature_segment_p2 = FeatureSegment.objects.create(
        segment=another_segment, feature=feature, environment=environment, priority=2
    )

    segment_override_p1 = FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment_p1
    )
    segment_override_p2 = FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment_p2
    )

    FeatureStateValue.objects.filter(feature_state=segment_override_p1).update(
        string_value="p1"
    )
    FeatureStateValue.objects.filter(feature_state=segment_override_p2).update(
        string_value="p2"
    )

    identity_model = mocker.MagicMock(
        environment_api_key=environment.api_key, identity_features=[]
    )

    # When
    feature_states, _ = get_all_feature_states_for_edge_identity(identity_model)

    # Then
    assert len(feature_states) == 1
    assert feature_states[0] == segment_override_p1

    dynamo_wrapper_mock.get_segment_ids.assert_called_once_with(
        identity_model=identity_model
    )
