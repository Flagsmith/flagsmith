import urllib
import uuid

from boto3.dynamodb.conditions import Key
from django.urls import reverse
from rest_framework import status


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
    mocker, admin_client, dynamo_enabled_environment, environment_api_key
):
    # Given
    identifier = "test_user123"
    identity_uuid = str(uuid.uuid4())
    identity_dict = {
        "composite_key": f"{environment_api_key}_{identifier}",
        "environment_api_key": environment_api_key,
        "identifier": identifier,
        "identity_uuid": identity_uuid,
    }
    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment_api_key, identity_uuid],
    )
    # When
    dynamo_identity_table = mocker.patch(
        "environments.identities.models.dynamo_identity_table"
    )
    dynamo_identity_table.query.return_value = {
        "Items": [identity_dict],
        "Count": 1,
    }

    response = admin_client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["identity_uuid"] == identity_uuid
    dynamo_identity_table.query.assert_called_with(
        IndexName="identity_uuid-index",
        Limit=1,
        KeyConditionExpression=Key("environment_api_key").eq(environment_api_key)
        & Key("identity_uuid").eq(identity_uuid),
    )


def test_create_identity_calls_put_item(
    mocker, admin_client, dynamo_enabled_environment, environment_api_key
):
    # Given
    identifier = "test_user123"

    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    dynamo_identity_table = mocker.patch(
        "environments.identities.models.dynamo_identity_table"
    )
    response = admin_client.post(url, data={"identifier": identifier})

    # Then, let's verify the function call
    # test that we only made one function call
    assert len(dynamo_identity_table.mock_calls) == 1
    name, args, kwargs = dynamo_identity_table.mock_calls[0]
    # With correct arguments
    assert name == "put_item"
    assert kwargs["Item"]["environment_api_key"] == environment_api_key
    assert kwargs["Item"]["identifier"] == identifier

    # Next, let's verify the response
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["identifier"] == identifier
    assert response.json()["identity_uuid"] is not None


def test_delete_identity_calls_delete_item(
    mocker, admin_client, dynamo_enabled_environment, environment_api_key
):
    # Given
    identifier = "test_user123"
    identity_dict = {
        "composite_key": f"{environment_api_key}_{identifier}",
        "environment_api_key": environment_api_key,
        "id": 0,
        "identifier": identifier,
        "created_date": "2021-09-29T13:28:20.839914+00:00",
    }
    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment_api_key, identifier],
    )
    # When
    dynamo_identity_table = mocker.patch(
        "environments.identities.models.dynamo_identity_table"
    )
    dynamo_identity_table.query.return_value = {
        "Items": [identity_dict],
        "Count": 1,
    }
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    dynamo_identity_table.delete_item.assert_called_with(
        Key={"composite_key": f"{environment_api_key}_{identifier}"}
    )


def test_identity_list_pagination(
    mocker, admin_client, dynamo_enabled_environment, environment_api_key
):
    # Given
    identifier = "test_user123"
    identity_dict = {
        "composite_key": f"{environment_api_key}_{identifier}",
        "environment_api_key": environment_api_key,
        "id": 0,
        "identifier": identifier,
        "created_date": "2021-09-29T13:28:20.839914+00:00",
    }
    # Firstly, let's setup the data
    identity_item_key = {
        k: v
        for k, v in identity_dict.items()
        if k in ["composite_key", "environment_api_key", "identifier"]
    }

    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )

    dynamo_identity_table = mocker.patch(
        "environments.identities.models.dynamo_identity_table"
    )

    dynamo_identity_table.query.return_value = {
        "Items": [identity_dict],
        "Count": 1,
        "LastEvaluatedKey": identity_item_key,
    }

    response = admin_client.get(url)
    # Test the response
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
    mocker, admin_client, dynamo_enabled_environment, environment_api_key
):
    # Given

    identifier = "test_user123"
    identity_dict = {
        "composite_key": f"{environment_api_key}_{identifier}",
        "environment_api_key": environment_api_key,
        "id": 0,
        "identifier": identifier,
        "created_date": "2021-09-29T13:28:20.839914+00:00",
    }
    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )

    dynamo_identity_table = mocker.patch(
        "environments.identities.models.dynamo_identity_table"
    )
    dynamo_identity_table.query.return_value = {
        "Items": [identity_dict],
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
    mocker, admin_client, dynamo_enabled_environment, environment_api_key
):
    # Given
    identifier = "test_user123"
    identity_dict = {
        "composite_key": f"{environment_api_key}_{identifier}",
        "environment_api_key": environment_api_key,
        "id": 0,
        "identifier": identifier,
        "created_date": "2021-09-29T13:28:20.839914+00:00",
    }
    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )

    url = "%s?q=%s" % (base_url, identifier)
    dynamo_identity_table = mocker.patch(
        "environments.identities.models.dynamo_identity_table"
    )

    dynamo_identity_table.query.return_value = {
        "Items": [identity_dict],
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
    mocker, admin_client, dynamo_enabled_environment, environment_api_key
):
    # Given
    identifier = "test_user123"
    identity_dict = {
        "composite_key": f"{environment_api_key}_{identifier}",
        "environment_api_key": environment_api_key,
        "id": 0,
        "identifier": identifier,
        "created_date": "2021-09-29T13:28:20.839914+00:00",
    }

    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    url = "%s?%s" % (
        base_url,
        urllib.parse.urlencode({"q": f'"{identifier}"'}),
    )
    dynamo_identity_table = mocker.patch(
        "environments.identities.models.dynamo_identity_table"
    )
    dynamo_identity_table.query.return_value = {
        "Items": [identity_dict],
        "Count": 1,
    }

    # When
    res = admin_client.get(url)

    # Then
    assert res.status_code == status.HTTP_200_OK

    # Add query is called with correct arguments
    dynamo_identity_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_api_key)
        & Key("identifier").eq(identifier),
    )
