from flag_engine.api.document_builders import build_identity_document
from flag_engine.identities.builders import build_identity_model

from edge_api.identities.serializers import EdgeIdentityFeatureStateSerializer


def test_edge_identity_feature_state_serializer_save_allows_missing_mvfsvs(
    mocker, identity, feature
):
    # Given
    identity_model = build_identity_model(build_identity_document(identity))
    view = mocker.MagicMock(identity=identity_model)

    serializer = EdgeIdentityFeatureStateSerializer(
        data={"feature_state_value": "foo", "feature": feature.id},
        context={"view": view},
    )

    mock_dynamo_wrapper = mocker.patch(
        "edge_api.identities.serializers.Identity.dynamo_wrapper"
    )

    # When
    serializer.is_valid(raise_exception=True)
    result = serializer.save()

    # Then
    assert result

    mock_dynamo_wrapper.put_item.assert_called_once()
    saved_identity_record = mock_dynamo_wrapper.put_item.call_args[0][0]
    assert saved_identity_record["identifier"] == identity.identifier
    assert len(saved_identity_record["identity_features"]) == 1

    saved_identity_feature_state = saved_identity_record["identity_features"][0]
    assert saved_identity_feature_state["multivariate_feature_state_values"] == []
    assert saved_identity_feature_state["featurestate_uuid"]
    assert saved_identity_feature_state["enabled"] is False
    assert saved_identity_feature_state["feature"]["id"] == feature.id
