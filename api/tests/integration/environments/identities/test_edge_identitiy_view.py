import urllib

import pytest
from boto3.dynamodb.conditions import Key
from django.urls import reverse
from rest_framework import status


@pytest.fixture()
def dynamo_identity_table(mocker):
    return mocker.patch(
        "environments.dynamodb.dynamodb_wrapper.DynamoIdentityWrapper._table"
    )


def test_get_identites_returns_bad_request_if_dynamo_is_not_enabled(
    admin_client, environment, environment_api_key
):
    # Given
    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_identity_calls_get_item(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    dynamo_identity_table,
):
    # Given
    identity_uuid = identity_document["identity_uuid"]

    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment_api_key, identity_uuid],
    )
    dynamo_identity_table.query.return_value = {
        "Items": [identity_document],
        "Count": 1,
    }

    # When
    response = admin_client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["identity_uuid"] == identity_uuid
    dynamo_identity_table.query.assert_called_with(
        IndexName="identity_uuid-index",
        Limit=1,
        KeyConditionExpression=Key("identity_uuid").eq(identity_uuid),
    )


def test_create_identity_calls_get_and_put_item(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    dynamo_identity_table,
):
    # Given
    identifier = "test_user123"

    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )

    dynamo_identity_table.get_item.return_value = {
        "Count": 0,
    }
    response = admin_client.post(url, data={"identifier": identifier})

    # Then, let's verify the function calls
    assert len(dynamo_identity_table.mock_calls) == 2
    # First call should be to check if an identity exists with
    # The same identifier
    name, args, kwargs = dynamo_identity_table.mock_calls[0]
    assert name == "get_item"
    assert args == ()
    assert kwargs == {"Key": {"composite_key": f"{environment_api_key}_{identifier}"}}

    # Second call should be to create(put) the item
    name, args, kwargs = dynamo_identity_table.mock_calls[1]
    assert name == "put_item"
    assert kwargs["Item"]["environment_api_key"] == environment_api_key
    assert kwargs["Item"]["identifier"] == identifier

    # Next, let's verify the response
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["identifier"] == identifier
    assert response.json()["identity_uuid"] is not None


def test_create_identity_returns_400_if_identity_already_exists(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    dynamo_identity_table,
):
    # Given
    identifier = identity_document["identifier"]

    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    dynamo_identity_table.get_item.return_value = {
        "Item": identity_document,
        "Count": 0,
    }
    response = admin_client.post(url, data={"identifier": identifier})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    dynamo_identity_table.put_item.assert_not_called()
    dynamo_identity_table.get_item.assert_called_with(
        Key={"composite_key": identity_document["composite_key"]}
    )


def test_delete_identity_calls_delete_item(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    dynamo_identity_table,
):
    # Given

    identifier = identity_document["identifier"]
    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment_api_key, identifier],
    )
    dynamo_identity_table.query.return_value = {
        "Items": [identity_document],
        "Count": 1,
    }

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    dynamo_identity_table.delete_item.assert_called_with(
        Key={"composite_key": identity_document["composite_key"]}
    )


def test_identity_list_pagination(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    dynamo_identity_table,
):
    # Firstly, let's setup the data
    identity_item_key = {
        k: v
        for k, v in identity_document.items()
        if k in ["composite_key", "environment_api_key", "identifier"]
    }

    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )

    dynamo_identity_table.query.return_value = {
        "Items": [identity_document],
        "Count": 1,
        "LastEvaluatedKey": identity_item_key,
    }

    response = admin_client.get(url)
    # Next, Test the response
    assert response.status_code == 200
    response = response.json()
    assert response["previous"] is None

    # Fetch the next url from the response since LastEvaluatedKey was part of the response from dynamodb
    next_url = response["next"]
    # Make the call using the next url
    response = admin_client.get(next_url)

    # And verify that .query was called with correct arguments
    dynamo_identity_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_api_key),
        ExclusiveStartKey=identity_item_key,
    )

    # And response does have previous url
    assert response.json()["previous"] is not None


def test_get_identities_list_calls_query_with_correct_arguments(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    dynamo_identity_table,
):
    # Given
    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )

    dynamo_identity_table.query.return_value = {
        "Items": [identity_document],
        "Count": 1,
    }

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    # Add query is called with correct arguments
    dynamo_identity_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_api_key),
    )


def test_search_identities_calls_query_with_correct_arguments(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    dynamo_identity_table,
):
    # Given
    identifier = identity_document["identifier"]

    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )

    url = "%s?q=%s" % (base_url, identifier)
    dynamo_identity_table.query.return_value = {
        "Items": [identity_document],
        "Count": 1,
    }

    # When
    response = admin_client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK

    # Add query is called with correct arguments
    dynamo_identity_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_api_key)
        & Key("identifier").begins_with(identifier),
    )


def test_search_for_identities_with_exact_match_calls_query_with_correct_argument(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    dynamo_identity_table,
):
    # Given
    identifier = identity_document["identifier"]

    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    url = "%s?%s" % (
        base_url,
        urllib.parse.urlencode({"q": f'"{identifier}"'}),
    )
    dynamo_identity_table.query.return_value = {
        "Items": [identity_document],
        "Count": 1,
    }

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Add query is called with correct arguments
    dynamo_identity_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_api_key)
        & Key("identifier").eq(identifier),
    )
