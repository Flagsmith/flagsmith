import json
import typing

import pytest
from core.constants import BOOLEAN, INTEGER, STRING
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient
from tests.integration.helpers import create_mv_option_with_api


def test_edge_identities_feature_states_list(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = identity_document

    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )
    # When
    response = admin_client.get(url)
    # Then
    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 3


def test_edge_identities_feature_states_list_can_be_filtered_using_feature_id(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = identity_document

    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )
    url = f"{url}?feature={feature}"
    # When
    response = admin_client.get(url)
    # Then
    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["feature"] == feature


def test_edge_identities_feature_states_list_returns_404_if_identity_does_not_exists(
    admin_client,
    environment,
    environment_api_key,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.side_effect = NotFound

    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, "identity_uuid_that_does_not_exists"],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_edge_identities_featurestate_detail(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = identity_document
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = identity_document["identity_features"][0]["featurestate_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    # When
    response = admin_client.get(url)

    # Then
    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["featurestate_uuid"] == featurestate_uuid


def test_edge_identities_featurestate_delete(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = identity_document
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = identity_document["identity_features"][0]["featurestate_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    # When
    response = admin_client.delete(url)

    # Then

    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)

    # Next, let's verify that deleted feature state
    # is not part of identity dict that we put
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    assert not list(
        filter(
            lambda fs: fs["featurestate_uuid"] == featurestate_uuid,
            args[0]["identity_features"],
        )
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_edge_identities_featurestate_delete_returns_404_if_featurestate_does_not_exists(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = identity_document
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = "some_random_uuid"
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_edge_identities_create_featurestate_returns_400_if_feature_state_already_exists(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = identity_document

    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )
    data = {
        "multivariate_feature_state_values": [],
        "enabled": True,
        "feature": feature,
        "feature_state_value": "random_value",
        "identity_uuid": "59efa2a7-6a45-46d6-b953-a7073a90eacf",
    }

    # When
    response = admin_client.post(url, data=data)

    # Then
    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_edge_identities_create_featurestate(
    admin_client,
    environment,
    environment_api_key,
    identity_document_without_fs,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document_without_fs
    )
    identity_uuid = identity_document_without_fs["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )
    expected_feature_state_value = "random_value"
    expected_fs_enabled = True
    data = {
        "multivariate_feature_state_values": [],
        "enabled": expected_fs_enabled,
        "feature": feature,
        "feature_state_value": expected_feature_state_value,
        "identity_uuid": identity_uuid,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == expected_feature_state_value

    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"

    # Next, let's verify that the document that we put
    # have the fs that we created

    # First, let's create the copy of the original document
    expected_identity_document = identity_document_without_fs
    # Next, let's append the fs that we created
    expected_identity_document["identity_features"].append(
        {
            "feature": {"type": "STANDARD", "name": "test_feature", "id": feature},
            "multivariate_feature_state_values": [],
            "enabled": expected_fs_enabled,
            "feature_segment": None,
            "feature_state_value": expected_feature_state_value,
            "django_id": None,
        }
    )
    # Remove the uuid before comparing because it was generated by the engine
    # and we can't patch it
    args[0]["identity_features"][0].pop("featurestate_uuid")

    # Finally, let's compare them
    assert args[0] == expected_identity_document


def test_edge_identities_create_mv_featurestate(
    admin_client,
    environment,
    environment_api_key,
    identity_document_without_fs,
    dynamo_wrapper_mock,
    feature,
    mv_option_50_percent,
    mv_option_value,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document_without_fs
    )
    identity_uuid = identity_document_without_fs["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )
    expected_feature_state_value = False
    expected_fs_enabled = True
    expected_percentage_allocation = 100
    data = {
        "feature": feature,
        "enabled": expected_fs_enabled,
        "multivariate_feature_state_values": [
            {
                "multivariate_feature_option": mv_option_50_percent,
                "percentage_allocation": expected_percentage_allocation,
            }
        ],
        "feature_state_value": expected_feature_state_value,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == mv_option_value

    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    # Next, let's verify that the document that we put
    # have the fs that we created

    # First, let's create the copy of the original document
    expected_identity_document = identity_document_without_fs
    # Next, let's append the fs that we created
    expected_identity_document["identity_features"].append(
        {
            "feature": {"type": "STANDARD", "name": "test_feature", "id": feature},
            "multivariate_feature_state_values": [
                {
                    "percentage_allocation": expected_percentage_allocation,
                    "id": None,
                    "multivariate_feature_option": {
                        "id": mv_option_50_percent,
                        "value": mv_option_value,
                    },
                }
            ],
            "enabled": expected_fs_enabled,
            "feature_state_value": expected_feature_state_value,
            "django_id": None,
            "feature_segment": None,
        }
    )
    # Remove the uuid before comparing because it was generated by the engine
    # and we can't patch it
    args[0]["identity_features"][0].pop("featurestate_uuid")
    args[0]["identity_features"][0]["multivariate_feature_state_values"][0].pop(
        "mv_fs_value_uuid"
    )
    # Finally, let's compare them
    assert args[0] == expected_identity_document


def test_edge_identities_update_featurestate(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = identity_document
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = identity_document["identity_features"][0]["featurestate_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    expected_feature_state_value = "new_feature_state_value"
    expected_fs_enabled = True
    data = {
        "multivariate_feature_state_values": [],
        "enabled": expected_fs_enabled,
        "feature": feature,
        "featurestate_uuid": featurestate_uuid,
        "feature_state_value": expected_feature_state_value,
        "identity_uuid": identity_uuid,
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == expected_feature_state_value
    assert response.json()["enabled"] == data["enabled"]

    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"

    # Next, let's verify that the document that we put
    # have correct updates

    # First, let's create the copy of the original document
    expected_identity_document = identity_document
    # Next, let's modify the fs value that we updated
    expected_identity_document["identity_features"][0][
        "feature_state_value"
    ] = expected_feature_state_value

    # Next, let's update the enabled
    expected_identity_document["identity_features"][0]["enabled"] = expected_fs_enabled

    # Finally, let's compare them
    assert args[0] == expected_identity_document


def test_edge_identities_patch_returns_405(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = identity_document
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = identity_document["identity_features"][0]["featurestate_uuid"]

    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    # When
    response = admin_client.patch(url, data={})
    # Then
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_edge_identities_update_mv_featurestate(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
    mv_option_50_percent,
    mv_option_value,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = identity_document
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = identity_document["identity_features"][2]["featurestate_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    new_mv_allocation = 100
    expected_feature_state_value = None
    expected_fs_enabled = True
    data = {
        "multivariate_feature_state_values": [
            {
                "percentage_allocation": new_mv_allocation,
                "multivariate_feature_option": mv_option_50_percent,
                "id": 1,
            },
        ],
        "enabled": expected_fs_enabled,
        "feature": feature,
        "featurestate_uuid": featurestate_uuid,
        "identity_uuid": identity_uuid,
        "feature_state_value": expected_feature_state_value,
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature_state_value"] == mv_option_value
    assert (
        response.json()["multivariate_feature_state_values"][0]["percentage_allocation"]
        == new_mv_allocation
    )

    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"

    # Next, let's verify that the document that we put
    # have correct updates

    # First, let's create the copy of the original document
    expected_identity_document = identity_document
    # Next, let's modify the fs value that we updated
    expected_identity_document["identity_features"][2][
        "feature_state_value"
    ] = expected_feature_state_value
    # Next, let's update the enabled
    expected_identity_document["identity_features"][2]["enabled"] = expected_fs_enabled

    # Now, we need to modify the `multivariate_feature_state_values`
    # for the fs that we updated
    expected_identity_document["identity_features"][2][
        "multivariate_feature_state_values"
    ] = [
        {
            "percentage_allocation": new_mv_allocation,
            "id": None,
            "multivariate_feature_option": {
                "id": mv_option_50_percent,
                "value": mv_option_value,
            },
        }
    ]
    # Remove the uuid before comparing because it was generated by the engine
    # and we can't patch it
    args[0]["identity_features"][2]["multivariate_feature_state_values"][0].pop(
        "mv_fs_value_uuid"
    )
    # Finally, let's compare them
    assert args[0] == expected_identity_document


def test_edge_identities_post_returns_400_for_invalid_mvfs_allocation(
    admin_client,
    project,
    environment,
    environment_api_key,
    identity_document_without_fs,
    dynamo_wrapper_mock,
    feature,
    mv_option_50_percent,
):

    # Given
    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document_without_fs
    )
    identity_uuid = identity_document_without_fs["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )
    mv_option_30_percent = create_mv_option_with_api(
        admin_client, project, feature, 30, "some_value"
    )

    data = {
        "feature": feature,
        "enabled": True,
        "multivariate_feature_state_values": [
            {
                "multivariate_feature_option": mv_option_50_percent,
                "percentage_allocation": 90,
            },
            {
                "multivariate_feature_option": mv_option_30_percent,
                "percentage_allocation": 90,
            },
        ],
        "feature_state_value": False,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["multivariate_feature_state_values"]
        == "Total percentage allocation for feature must be less than 100 percent"
    )


def test_edge_identities_with_identifier_create_featurestate(
    admin_client,
    environment,
    environment_api_key,
    identity_document_without_fs,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item.return_value = identity_document_without_fs
    identity_identifier = identity_document_without_fs["identifier"]
    url = reverse(
        "api-v1:environments:edge-identities-with-identifier-featurestates-create-or-update",
        args=[environment_api_key],
    )
    expected_feature_state_value = "random_value"
    expected_fs_enabled = True
    data = {
        "multivariate_feature_state_values": [],
        "enabled": expected_fs_enabled,
        "feature": feature,
        "feature_state_value": expected_feature_state_value,
        "identifier": identity_identifier,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == expected_feature_state_value

    dynamo_wrapper_mock.get_item.assert_called_with(
        f"{environment_api_key}_{identity_identifier}"
    )
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"

    # Next, let's verify that the document that we put
    # have the fs that we created

    assert len(args[0]["identity_features"]) == 1
    actual_feature_state = args[0]["identity_features"][0]

    assert actual_feature_state["feature"] == {
        "type": "STANDARD",
        "name": "test_feature",
        "id": feature,
    }

    assert actual_feature_state["enabled"] == expected_fs_enabled
    assert actual_feature_state["feature_state_value"] == expected_feature_state_value
    assert actual_feature_state["multivariate_feature_state_values"] == []
    assert actual_feature_state["featurestate_uuid"] is not None


def test_edge_identities_with_identifier_featurestate_delete(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item.return_value = identity_document
    identifier = identity_document["identifier"]
    url = reverse(
        "api-v1:environments:edge-identities-with-identifier-featurestates-remove",
        args=[environment_api_key],
    )
    data = {"identifier": identifier, "feature": feature}

    # When
    response = admin_client.delete(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    dynamo_wrapper_mock.get_item.assert_called_with(
        f"{environment_api_key}_{identifier}"
    )

    # Next, let's verify that deleted feature state
    # is not part of identity dict that we put
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    assert not list(
        filter(
            lambda fs: fs["feature"]["id"] == feature,
            args[0]["identity_features"],
        )
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_edge_identities_with_identifier_update_featurestate(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item.return_value = identity_document
    identifier = identity_document["identifier"]
    url = reverse(
        "api-v1:environments:edge-identities-with-identifier-featurestates-create-or-update",
        args=[environment_api_key],
    )
    expected_feature_state_value = "new_feature_state_value"
    expected_fs_enabled = True
    data = {
        "multivariate_feature_state_values": [],
        "enabled": expected_fs_enabled,
        "feature": feature,
        "feature_state_value": expected_feature_state_value,
        "identifier": identifier,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == expected_feature_state_value
    assert response.json()["enabled"] == data["enabled"]
    dynamo_wrapper_mock.get_item.assert_called_with(
        f"{environment_api_key}_{identifier}"
    )
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"

    # Next, let's verify that the document that we put
    # have correct updates

    # First, let's modify the fs value that we updated
    identity_document["identity_features"][0][
        "feature_state_value"
    ] = expected_feature_state_value

    # Next, let's update the enabled
    identity_document["identity_features"][0]["enabled"] = expected_fs_enabled

    # Finally, let's compare them
    assert args[0] == identity_document


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
    identity_document_without_fs,
    dynamo_wrapper_mock,
    project,
    feature,
    feature_name,
    segment,
    segment_name,
    default_feature_value,
    segment_override_type,
    segment_override_value,
):
    # Mock the get_segment_ids method so that it returns no segments for the first
    # request (to get the environment default), then so that it returns one segment
    # for the segment and identity override requests.
    segment_ids_responses = [[], [segment], [segment]]

    def get_segment_ids_side_effect(*args, **kwargs):
        nonlocal segment_ids_responses
        return segment_ids_responses.pop(0)

    dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document_without_fs
    )
    dynamo_wrapper_mock.get_segment_ids.side_effect = get_segment_ids_side_effect

    # First, let's verify that, without any overrides, the endpoint gives us the
    # environment default feature state
    get_all_identity_feature_states_url = reverse(
        "api-v1:environments:edge-identity-featurestates-all",
        args=(environment_api_key, identity_document_without_fs["identity_uuid"]),
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
    _create_segment_override(
        client=admin_client,
        environment_id=environment,
        feature_id=feature,
        segment_id=segment,
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
    assert second_response_json[0]["segment"]["id"] == segment
    assert second_response_json[0]["segment"]["name"] == segment_name

    # finally, let's simulate an override for the identity
    identity_override_value = "identity override"
    identity_document_without_fs["identity_features"] = [
        {
            "featurestate_uuid": "ad71c644-71df-4e83-9cb5-cd2cd0160200",
            "multivariate_feature_state_values": [],
            "feature_state_value": identity_override_value,
            "django_id": 1,
            "feature": {
                "name": feature_name,
                "type": "STANDARD",
                "id": feature,
            },
            "enabled": True,
            "feature_segment": None,
        }
    ]

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
    feature_id: int,
    segment_id: int,
    segment_override_value: typing.Union[str, int, bool],
    segment_override_type: str,
):
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
