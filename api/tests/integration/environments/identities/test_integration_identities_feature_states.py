import json
import typing

import pytest
from core.constants import BOOLEAN, INTEGER, STRING
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.parametrize(
    "segment_override_type, segment_override_value",
    (
        ("unicode", "foo"),
        ("int", 42),
        ("bool", True),
    ),
)
def test_get_all_feature_states_for_an_identity(
    admin_client,
    environment,
    environment_api_key,
    project,
    feature,
    feature_name,
    default_feature_value,
    identity,
    segment_override_type,
    segment_override_value,
):
    # First, let's verify that, without any overrides, the endpoint gives us the
    # environment default feature state
    get_all_identity_feature_states_url = reverse(
        "api-v1:environments:identity-featurestates-all",
        args=(environment_api_key, identity),
    )
    first_response = admin_client.get(get_all_identity_feature_states_url)

    assert first_response.status_code == status.HTTP_200_OK

    first_response_json = first_response.json()
    assert len(first_response_json) == 1
    assert first_response_json[0]["feature"]["id"] == feature
    assert (
        first_response_json[0]["enabled"] is False
    )  # based on information in fixtures
    assert first_response_json[0]["feature_state_value"] == default_feature_value
    assert first_response_json[0]["overridden_by"] is None
    assert first_response_json[0]["segment"] is None

    # now, let's create a segment and override the feature
    segment_id, segment_name = _create_segment_override(
        client=admin_client,
        environment_id=environment,
        environment_api_key=environment_api_key,
        feature_id=feature,
        project_id=project,
        identity_id=identity,
        segment_override_type=segment_override_type,
        segment_override_value=segment_override_value,
    )

    # and check the response now correctly shows the segment override
    second_response = admin_client.get(get_all_identity_feature_states_url)

    assert second_response.status_code == status.HTTP_200_OK

    second_response_json = second_response.json()
    assert len(second_response_json) == 1
    assert second_response_json[0]["feature"]["id"] == feature
    assert (
        second_response_json[0]["enabled"] is True
    )  # segment override helper sets to true
    assert second_response_json[0]["feature_state_value"] == segment_override_value
    assert second_response_json[0]["overridden_by"] == "SEGMENT"
    assert second_response_json[0]["segment"]["id"] == segment_id
    assert second_response_json[0]["segment"]["name"] == segment_name

    # finally, let's simulate an override for the identity
    identity_override_value = "identity override"
    identity_feature_states_url = reverse(
        "api-v1:environments:identity-featurestates-list",
        args=(environment_api_key, identity),
    )
    create_identity_feature_state_response = admin_client.post(
        identity_feature_states_url,
        data=json.dumps(
            {
                "feature": feature,
                "enabled": True,
                "feature_state_value": identity_override_value,
            }
        ),
        content_type="application/json",
    )
    assert create_identity_feature_state_response.status_code == status.HTTP_201_CREATED

    # and check the response now correctly shows the identity override
    third_response = admin_client.get(get_all_identity_feature_states_url)

    assert third_response.status_code == status.HTTP_200_OK

    third_response_json = third_response.json()
    assert len(third_response_json) == 1
    assert third_response_json[0]["feature"]["id"] == feature
    assert third_response_json[0]["enabled"] is True  # set to true manually above
    assert third_response_json[0]["feature_state_value"] == identity_override_value
    assert third_response_json[0]["overridden_by"] == "IDENTITY"
    assert third_response_json[0]["segment"] is None


def _create_segment_override(
    client: APIClient,
    environment_id: int,
    environment_api_key: str,
    project_id: int,
    feature_id: int,
    identity_id: int,
    segment_override_value: typing.Union[str, int, bool],
    segment_override_type: str,
):
    # create the segment
    trait_key = "foo"
    trait_value = "bar"
    segment_name = "segment"

    create_segment_url = reverse(
        "api-v1:projects:project-segments-list", args=[project_id]
    )
    create_segment_response = client.post(
        create_segment_url,
        json.dumps(
            {
                "name": segment_name,
                "project": project_id,
                "rules": [
                    {
                        "type": "ALL",
                        "conditions": [
                            {
                                "operator": "EQUAL",
                                "property": trait_key,
                                "value": trait_value,
                            }
                        ],
                    }
                ],
            }
        ),
        content_type="application/json",
    )
    assert create_segment_response.status_code == status.HTTP_201_CREATED
    segment_id = create_segment_response.json()["id"]

    # create the feature segment for the feature / segment combination
    create_feature_segment_url = reverse("api-v1:features:feature-segment-list")
    data = {
        "feature": feature_id,
        "segment": segment_id,
        "environment": environment_id,
    }
    create_feature_segment_response = client.post(create_feature_segment_url, data)
    assert create_feature_segment_response.status_code == status.HTTP_201_CREATED
    feature_segment_id = create_feature_segment_response.json()["id"]

    # add the trait to the identity
    create_trait_url = reverse(
        "api-v1:environments:identities-traits-list",
        args=[environment_api_key, identity_id],
    )
    create_trait_response = client.post(
        create_trait_url,
        data=json.dumps({"trait_key": trait_key, "string_value": trait_value}),
        content_type="application/json",
    )
    assert create_trait_response.status_code == status.HTTP_201_CREATED

    # now, let's create the segment override for the feature
    create_segment_override_url = reverse("api-v1:features:featurestates-list")
    data = {
        "feature": feature_id,
        "feature_segment": feature_segment_id,
        "feature_state_value": {
            "type": segment_override_type,
            "string_value": segment_override_value
            if segment_override_type == STRING
            else None,
            "integer_value": segment_override_value
            if segment_override_type == INTEGER
            else None,
            "boolean_value": segment_override_value
            if segment_override_type == BOOLEAN
            else None,
        },
        "enabled": True,
        "environment": environment_id,
    }
    create_segment_override_response = client.post(
        create_segment_override_url,
        data=json.dumps(data),
        content_type="application/json",
    )
    assert create_segment_override_response.status_code == status.HTTP_201_CREATED

    return segment_id, segment_name
