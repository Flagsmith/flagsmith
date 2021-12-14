import pytest
from django.urls import reverse
from rest_framework import status


@pytest.fixture()
def dynamo_wrapper_mock(mocker):
    return mocker.patch(
        "environments.identities.models.Identity.dynamo_wrapper",
    )


def test_edge_identities_feature_states_list(
    mocker,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid.return_value = identity_document

    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )
    # When
    response = admin_client.get(url)
    # Then
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        environment_api_key, identity_uuid
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 3


def test_edge_identities_featurestate_detail(
    mocker,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid.return_value = identity_document
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = identity_document["identity_features"][0]["featurestate_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    # When
    response = admin_client.get(url)

    # Then
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        environment_api_key, identity_uuid
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["featurestate_uuid"] == featurestate_uuid


def test_edge_identities_featurestate_delete(
    mocker,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid.return_value = identity_document
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = identity_document["identity_features"][0]["featurestate_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    # When
    response = admin_client.delete(url)

    # Then
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        environment_api_key, identity_uuid
    )
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


def test_edge_identities_create_featurestate_returns_400_if_feature_state_already_exists(
    mocker,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid.return_value = identity_document

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
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        environment_api_key, identity_uuid
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_edge_identities_create_featurestate(
    mocker,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid.return_value = identity_document
    # Remove the already preset feature state form the fixture document
    identity_document["identity_features"].pop(0)
    identity_uuid = identity_document["identity_uuid"]
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
    response = admin_client.post(url, data=data)
    # Then
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        environment_api_key, identity_uuid
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == feature_state_value


def test_edge_identities_udpate_featurestate(
    mocker,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    dynamo_wrapper_mock,
    feature,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid.return_value = identity_document
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
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        environment_api_key, identity_uuid
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == feature_state_value
