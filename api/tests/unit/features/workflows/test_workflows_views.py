import json

from django.urls import reverse
from rest_framework import status

from features.models import FeatureState
from features.workflows.models import ChangeRequest


def test_create_change_request(
    feature, environment, admin_client, organisation_one_user
):
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    data = {
        "title": "My change request",
        "description": "Some useful description",
        "from_feature_state": feature_state.id,
        "to_feature_state": {
            "enabled": True,
            "feature_state_value": {"type": "unicode", "string_value": "foobar"},
            "multivariate_feature_state_values": [],
        },
        "approvals": [{"user": organisation_one_user.id, "required": True}],
    }
    url = reverse("api-v1:features:workflows:change-requests-list")

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    # The request is successful
    assert response.status_code == status.HTTP_201_CREATED

    # and the change request is stored and the correct values are updated
    response_json = response.json()
    assert response_json["id"]
    assert response_json["created_at"]
    assert response_json["updated_at"]

    # and it has the correct approvals
    change_request = ChangeRequest.objects.get(id=response_json["id"])
    assert change_request.approvals.count() == 1
    assert change_request.approvals.first().user == organisation_one_user

    # and the to_feature_state object is created with the expected information
    to_feature_state_id = response_json["to_feature_state"]["id"]
    to_feature_state = FeatureState.objects.get(id=to_feature_state_id)
    assert to_feature_state.environment == feature_state.environment
    assert to_feature_state.feature == feature_state.feature
    assert to_feature_state.feature_segment == feature_state.feature_segment
    assert to_feature_state.identity == feature_state.identity
    assert to_feature_state.version is None
    assert to_feature_state.live_from is None
    assert (
        to_feature_state.get_feature_state_value()
        == data["to_feature_state"]["feature_state_value"]["string_value"]
    )
