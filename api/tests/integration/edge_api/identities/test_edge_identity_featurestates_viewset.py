import json
import typing
import uuid

import pytest
from core.constants import BOOLEAN, INTEGER, STRING
from django.urls import reverse
from flag_engine.features.models import FeatureModel, FeatureStateModel
from mypy_boto3_dynamodb.service_resource import Table
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient

from edge_api.identities.models import (
    EdgeIdentity,
    IdentityFeaturesList,
    IdentityModel,
)
from features.models import Feature
from projects.models import Project
from tests.integration.helpers import create_mv_option_with_api
from util.mappers.engine import map_feature_to_engine


def test_edge_identities_feature_states_list_does_not_call_sync_identity_document_features_if_not_needed(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
    mocker,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    sync_identity_document_features = mocker.patch(
        "edge_api.identities.models.sync_identity_document_features"
    )
    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )
    # When
    response = admin_client.get(url)
    # Then
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 3
    sync_identity_document_features.delay.assert_not_called()


def test_edge_identities_feature_states_list_calls_sync_identity_document_features_if_identity_have_deleted_feature(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
    mocker,
):
    # Given
    sync_identity_document_features = mocker.patch(
        "edge_api.identities.models.sync_identity_document_features"
    )
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    identity_uuid = identity_document["identity_uuid"]
    deleted_feature_id = 9999
    # First, let's add a feature to the identity that is not in the environment
    identity_document["identity_features"].append(
        {
            "feature_state_value": "feature_1_value",
            "django_id": 1,
            "feature": {
                "name": "feature_that_does_not_exists",
                "type": "STANDARD",
                "id": deleted_feature_id,
            },
            "enabled": True,
        }
    )
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )

    # When
    response = admin_client.get(url)

    # Then
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 3
    # And deleted feature is not part of the response
    assert not list(
        filter(
            lambda fs: fs["feature"] == deleted_feature_id,
            response.json(),
        )
    )

    sync_identity_document_features.delay.assert_called_once_with(args=(identity_uuid,))


def test_edge_identities_feature_states_list_can_be_filtered_using_feature_id(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
    feature,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )

    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-list",
        args=[environment_api_key, identity_uuid],
    )
    url = f"{url}?feature={feature}"
    # When
    response = admin_client.get(url)
    # Then
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["feature"] == feature


def test_edge_identities_feature_states_list_returns_404_if_identity_does_not_exists(
    admin_client,
    environment,
    environment_api_key,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.side_effect = NotFound

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
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = identity_document["identity_features"][0]["featurestate_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    # When
    response = admin_client.get(url)

    # Then
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["featurestate_uuid"] == featurestate_uuid


def test_edge_identities_featurestate_detail_calls_sync_identity_if_deleted_feature_exists(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
    mocker,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    identity_uuid = identity_document["identity_uuid"]
    sync_identity_document_features = mocker.patch(
        "edge_api.identities.models.sync_identity_document_features"
    )
    # let's add a feature to the identity that is not in the environment
    deleted_feature_id = 9999
    deleted_featurestate_uuid = "4a8fbe06-d4cd-4686-a184-d924844bb422"
    identity_document["identity_features"].append(
        {
            "feature_state_value": "feature_1_value",
            "featurestate_uuid": deleted_featurestate_uuid,
            "django_id": 1,
            "feature": {
                "name": "feature_that_does_not_exists",
                "type": "STANDARD",
                "id": deleted_feature_id,
            },
            "enabled": True,
        }
    )
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, deleted_featurestate_uuid],
    )
    # When - asked for that featurestate
    response = admin_client.get(url)

    # Then
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    sync_identity_document_features.delay.assert_called_once_with(args=(identity_uuid,))


def test_edge_identities_featurestate_delete(
    dynamodb_wrapper_v2,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    identity_uuid = identity_document["identity_uuid"]
    featurestate_uuid = identity_document["identity_features"][0]["featurestate_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-detail",
        args=[environment_api_key, identity_uuid, featurestate_uuid],
    )
    # When
    response = admin_client.delete(url)

    # Then

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )

    # Next, let's verify that deleted feature state
    # is not part of identity dict that we put
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
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
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
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
    edge_identity_dynamo_wrapper_mock,
    feature,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )

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
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_edge_identities_create_featurestate(
    dynamodb_wrapper_v2,
    admin_client,
    environment,
    environment_api_key,
    identity_document_without_fs,
    edge_identity_dynamo_wrapper_mock,
    feature,
    feature_name,
    webhook_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
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

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"

    # Next, let's verify that the document that we put
    # have the fs that we created

    assert len(args[0]["identity_features"]) == 1
    actual_feature_state = args[0]["identity_features"][0]

    assert actual_feature_state["feature"] == {
        "type": "STANDARD",
        "name": feature_name,
        "id": feature,
    }

    assert actual_feature_state["enabled"] == expected_fs_enabled
    assert actual_feature_state["feature_state_value"] == expected_feature_state_value
    assert actual_feature_state["multivariate_feature_state_values"] == []
    assert actual_feature_state["featurestate_uuid"] is not None


def test_edge_identities_create_mv_featurestate(
    dynamodb_wrapper_v2,
    admin_client,
    environment,
    environment_api_key,
    identity_document_without_fs,
    edge_identity_dynamo_wrapper_mock,
    feature,
    mv_option_50_percent,
    mv_option_value,
    feature_name,
    webhook_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
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

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"

    # Next, let's verify that the document that we put
    # have the fs that we created
    assert len(args[0]["identity_features"]) == 1
    actual_feature_state = args[0]["identity_features"][0]

    assert actual_feature_state["feature"] == {
        "type": "MULTIVARIATE",
        "name": feature_name,
        "id": feature,
    }

    assert actual_feature_state["enabled"] == expected_fs_enabled
    assert actual_feature_state["feature_state_value"] == expected_feature_state_value

    assert len(actual_feature_state["multivariate_feature_state_values"]) == 1

    actual_mv_fs_value = actual_feature_state["multivariate_feature_state_values"][0]

    assert actual_mv_fs_value["percentage_allocation"] == expected_percentage_allocation
    assert actual_mv_fs_value["mv_fs_value_uuid"] is not None
    assert (
        actual_mv_fs_value["multivariate_feature_option"]["id"] == mv_option_50_percent
    )
    assert actual_mv_fs_value["multivariate_feature_option"]["value"] == mv_option_value

    assert actual_feature_state["featurestate_uuid"] is not None


def test_edge_identities_update_featurestate(
    dynamodb_wrapper_v2,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
    feature,
    webhook_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
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

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
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
    edge_identity_dynamo_wrapper_mock,
    feature,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
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
    dynamodb_wrapper_v2,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
    feature,
    mv_option_50_percent,
    mv_option_value,
    webhook_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
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

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
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
    edge_identity_dynamo_wrapper_mock,
    feature,
    mv_option_50_percent,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
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
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "multivariate_feature_state_values" in response.json()


@pytest.mark.parametrize(
    "lazy_feature", [(lazy_fixture("feature")), (lazy_fixture("feature_name"))]
)
def test_edge_identities_with_identifier_create_featurestate(
    dynamodb_wrapper_v2,
    admin_client,
    environment,
    environment_api_key,
    identity_document_without_fs,
    edge_identity_dynamo_wrapper_mock,
    feature,
    feature_name,
    lazy_feature,
    webhook_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item.return_value = (
        identity_document_without_fs
    )
    identity_identifier = identity_document_without_fs["identifier"]
    url = reverse(
        "api-v1:environments:edge-identities-with-identifier-featurestates",
        args=[environment_api_key],
    )
    expected_feature_state_value = "random_value"
    expected_fs_enabled = True
    data = {
        "multivariate_feature_state_values": [],
        "enabled": expected_fs_enabled,
        "feature": lazy_feature,
        "feature_state_value": expected_feature_state_value,
        "identifier": identity_identifier,
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == expected_feature_state_value

    edge_identity_dynamo_wrapper_mock.get_item.assert_called_with(
        f"{environment_api_key}_{identity_identifier}"
    )
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"

    # Next, let's verify that the document that we put
    # have the fs that we created

    actual_feature_state = args[0]["identity_features"][0]
    assert actual_feature_state["feature"] == {
        "type": "STANDARD",
        "name": feature_name,
        "id": feature,
    }

    assert actual_feature_state["enabled"] == expected_fs_enabled
    assert actual_feature_state["feature_state_value"] == expected_feature_state_value
    assert actual_feature_state["multivariate_feature_state_values"] == []
    assert actual_feature_state["featurestate_uuid"] is not None


@pytest.mark.parametrize(
    "lazy_feature", [(lazy_fixture("feature")), (lazy_fixture("feature_name"))]
)
def test_edge_identities_with_identifier_delete_featurestate(
    dynamodb_wrapper_v2,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
    feature,
    lazy_feature,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item.return_value = identity_document
    identifier = identity_document["identifier"]
    url = reverse(
        "api-v1:environments:edge-identities-with-identifier-featurestates",
        args=[environment_api_key],
    )
    data = {"identifier": identifier, "feature": lazy_feature}

    # When
    response = admin_client.delete(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    edge_identity_dynamo_wrapper_mock.get_item.assert_called_with(
        f"{environment_api_key}_{identifier}"
    )

    # Next, let's verify that deleted feature state
    # is not part of identity dict that we put
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    assert not list(
        filter(
            lambda fs: fs["feature"]["id"] == feature,
            args[0]["identity_features"],
        )
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_edge_identities_with_identifier_update_featurestate(
    dynamodb_wrapper_v2,
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
    feature,
    webhook_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item.return_value = identity_document
    identifier = identity_document["identifier"]
    url = reverse(
        "api-v1:environments:edge-identities-with-identifier-featurestates",
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
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["feature"] == feature
    assert response.json()["feature_state_value"] == expected_feature_state_value
    assert response.json()["enabled"] == data["enabled"]
    edge_identity_dynamo_wrapper_mock.get_item.assert_called_with(
        f"{environment_api_key}_{identifier}"
    )
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
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
    edge_identity_dynamo_wrapper_mock,
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

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document_without_fs
    )
    edge_identity_dynamo_wrapper_mock.get_segment_ids.side_effect = (
        get_segment_ids_side_effect
    )

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
            "string_value": (
                segment_override_value if segment_override_type == STRING else None
            ),
            "integer_value": (
                segment_override_value if segment_override_type == INTEGER else None
            ),
            "boolean_value": (
                segment_override_value if segment_override_type == BOOLEAN else None
            ),
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


def test_edge_identity_clone_flag_states_from(
    admin_client: APIClient,
    app_settings_for_dynamodb: None,
    dynamo_enabled_environment: int,
    dynamo_enabled_project: int,
    environment_api_key: str,
    flagsmith_identities_table: Table,
) -> None:
    def create_identity(identifier: str) -> EdgeIdentity:
        identity_model = IdentityModel(
            identifier=identifier,
            environment_api_key=environment_api_key,
            identity_features=IdentityFeaturesList(),
            identity_uuid=uuid.uuid4(),
        )
        return EdgeIdentity(engine_identity_model=identity_model)

    def features_for_identity_clone_flag_states_from(
        project: Project,
    ) -> tuple[Feature, ...]:
        features: list[Feature] = []
        for i in range(1, 4):
            features.append(
                Feature.objects.create(
                    name=f"feature_{i}", project=project, default_enabled=True
                )
            )
        return tuple(features)

    # Given
    project: Project = Project.objects.get(id=dynamo_enabled_project)

    feature_1, feature_2, feature_3 = features_for_identity_clone_flag_states_from(
        project
    )

    feature_model_1: FeatureModel = map_feature_to_engine(feature=feature_1)
    feature_model_2: FeatureModel = map_feature_to_engine(feature=feature_2)
    feature_model_3: FeatureModel = map_feature_to_engine(feature=feature_3)

    source_identity: EdgeIdentity = create_identity(identifier="source_identity")
    target_identity: EdgeIdentity = create_identity(identifier="target_identity")

    source_feature_state_1_value = "Source Identity for feature value 1"
    source_feature_state_1 = FeatureStateModel(
        feature=feature_model_1,
        environment_id=dynamo_enabled_environment,
        enabled=True,
        feature_state_value=source_feature_state_1_value,
    )

    source_feature_state_2_value = "Source Identity for feature value 2"
    source_feature_state_2 = FeatureStateModel(
        feature=feature_model_2,
        environment_id=dynamo_enabled_environment,
        enabled=True,
        feature_state_value=source_feature_state_2_value,
    )

    target_feature_state_2_value = "Target Identity value for feature 2"
    target_feature_state_2 = FeatureStateModel(
        feature=feature_model_2,
        environment_id=dynamo_enabled_environment,
        enabled=False,
        feature_state_value=target_feature_state_2_value,
    )

    target_feature_state_3 = FeatureStateModel(
        feature=feature_model_3,
        environment_id=dynamo_enabled_environment,
        enabled=False,
    )

    # Add feature states for features 1 and 2 to source identity
    source_identity.add_feature_override(feature_state=source_feature_state_1)
    source_identity.add_feature_override(feature_state=source_feature_state_2)

    # Add feature states for features 2 and 3 to target identity.
    target_identity.add_feature_override(feature_state=target_feature_state_2)
    target_identity.add_feature_override(feature_state=target_feature_state_3)

    # Save identities to table
    target_identity_document = target_identity.to_document()
    source_identity_document = source_identity.to_document()

    flagsmith_identities_table.put_item(Item=target_identity_document)
    flagsmith_identities_table.put_item(Item=source_identity_document)

    clone_from_given_identity_url: str = reverse(
        viewname="api-v1:environments:edge-identity-featurestates-clone-from-given-identity",
        args=(environment_api_key, target_identity.identity_uuid),
    )

    # When

    clone_identity_feature_states_response = admin_client.post(
        path=clone_from_given_identity_url,
        data=json.dumps(
            obj={"source_identity_uuid": str(object=source_identity.identity_uuid)}
        ),
        content_type="application/json",
    )

    # Then

    assert clone_identity_feature_states_response.status_code == status.HTTP_200_OK

    response = clone_identity_feature_states_response.json()

    # Target identity contains only the 2 cloned overridden features states and 1 environment feature state
    assert len(response) == 3

    assert response[0]["feature"]["id"] == feature_1.id
    assert response[0]["enabled"] == source_feature_state_1.enabled
    assert response[0]["feature_state_value"] == source_feature_state_1_value
    assert response[0]["overridden_by"] == "IDENTITY"

    assert response[1]["feature"]["id"] == feature_2.id
    assert response[1]["enabled"] == source_feature_state_2.enabled
    assert response[1]["feature_state_value"] == source_feature_state_2_value
    assert response[1]["overridden_by"] == "IDENTITY"

    assert response[2]["feature"]["id"] == feature_3.id
    assert response[2]["enabled"] == feature_3.default_enabled
    assert response[2]["feature_state_value"] == feature_3.initial_value
    assert response[2]["overridden_by"] is None
