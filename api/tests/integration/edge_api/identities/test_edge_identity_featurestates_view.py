import json

from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import NotFound


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
    feature_state_value = "random_value"
    data = {
        "multivariate_feature_state_values": [],
        "enabled": True,
        "feature": feature,
        "feature_state_value": feature_state_value,
        "identity_uuid": identity_uuid,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == feature_state_value


def test_edge_identities_create_mv_featurestate(
    admin_client,
    environment,
    environment_api_key,
    identity_document_without_fs,
    dynamo_wrapper_mock,
    feature,
    mv_option,
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

    data = {
        "feature": feature,
        "enabled": True,
        "multivariate_feature_state_values": [
            {
                "multivariate_feature_option": mv_option,
                "multivariate_feature_option_index": 0,
                "percentage_allocation": 100,
            }
        ],
        "feature_state_value": False,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == mv_option_value


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
    feature_state_value = "new_feature_state_value"
    data = {
        "multivariate_feature_state_values": [],
        "enabled": True,
        "feature": feature,
        "featurestate_uuid": featurestate_uuid,
        "feature_state_value": feature_state_value,
        "identity_uuid": identity_uuid,
    }

    # When
    response = admin_client.put(url, data=data)
    # Then
    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == feature_state_value


def test_edge_identities_update_mv_featurestate(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
    mv_option,
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
    data = {
        "multivariate_feature_state_values": [
            {
                "percentage_allocation": new_mv_allocation,
                "multivariate_feature_option": mv_option,
                "id": 1,
            },
        ],
        "enabled": True,
        "feature": feature,
        "featurestate_uuid": featurestate_uuid,
        "identity_uuid": identity_uuid,
        "feature_state_value": None,
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(identity_uuid)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature_state_value"] == mv_option_value
    assert (
        response.json()["multivariate_feature_state_values"][0]["percentage_allocation"]
        == new_mv_allocation
    )


def test_edge_identities_post_returns_400_for_invalid_mvfs_allocation(
    admin_client,
    environment,
    environment_api_key,
    identity_document_without_fs,
    dynamo_wrapper_mock,
    feature,
    mv_option,
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

    data = {
        "feature": feature,
        "enabled": True,
        "multivariate_feature_state_values": [
            {
                "multivariate_feature_option": mv_option,
                "percentage_allocation": 90,
            },
            {
                "multivariate_feature_option": mv_option,
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
