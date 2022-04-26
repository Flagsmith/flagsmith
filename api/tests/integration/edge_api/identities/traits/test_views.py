import json

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from rest_framework import status


def test_edge_identities_traits_list(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    identity_traits,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid.return_value = identity_document

    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:edge-identity-traits-list",
        args=[environment_api_key, identity_uuid],
    )
    # When
    response = admin_client.get(url)
    # Then
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        environment_api_key, identity_uuid
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == identity_traits


def test_edge_identities_traits_list_returns_404_if_identity_does_not_exists(
    admin_client,
    environment,
    environment_api_key,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid.side_effect = ObjectDoesNotExist

    url = reverse(
        "api-v1:environments:edge-identity-traits-list",
        args=[environment_api_key, "identity_uuid_that_does_not_exists"],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_edge_identities_traits_create_trait(
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
        "api-v1:environments:edge-identity-traits-create-or-update",
        args=[environment_api_key, identity_uuid],
    )
    trait_key = "new_trait_key"
    data = {"trait_key": trait_key, "trait_value": "new_trait_value"}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        environment_api_key, identity_uuid
    )
    # Next, let's verify that new trait
    # is part of identity dict that we put
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    assert list(
        filter(
            lambda trait: trait["trait_key"] == trait_key,
            args[0]["identity_traits"],
        )
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["trait_key"] == trait_key


def test_edge_identities_traits_update_trait(
    admin_client,
    environment,
    environment_api_key,
    identity_document,
    identity_traits,
    dynamo_wrapper_mock,
):
    # Given
    dynamo_wrapper_mock.get_item_from_uuid.return_value = identity_document
    identity_uuid = identity_document["identity_uuid"]
    trait_key = identity_traits[0]["trait_key"]
    url = reverse(
        "api-v1:environments:edge-identity-traits-create-or-update",
        args=[environment_api_key, identity_uuid],
    )
    updated_trait_value = "updated_trait_value"
    data = {"trait_key": trait_key, "trait_value": updated_trait_value}

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    dynamo_wrapper_mock.get_item_from_uuid.assert_called_with(
        environment_api_key, identity_uuid
    )
    # Next, let's verify that updated trait value
    # is part of identity dict that we put
    name, args, _ = dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    assert list(
        filter(
            lambda trait: trait["trait_key"] == trait_key
            and trait["trait_value"] == updated_trait_value,
            args[0]["identity_traits"],
        )
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["trait_key"] == trait_key
    assert response.json()["trait_value"] == updated_trait_value
