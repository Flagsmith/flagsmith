import json
import urllib
from typing import Any

from boto3.dynamodb.conditions import Key
from django.urls import reverse
from mypy_boto3_dynamodb.service_resource import Table
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient

from edge_api.identities.search import DASHBOARD_ALIAS_SEARCH_PREFIX
from environments.dynamodb.wrappers.environment_wrapper import (
    DynamoEnvironmentV2Wrapper,
)
from environments.dynamodb.wrappers.identity_wrapper import (
    DynamoIdentityWrapper,
)
from environments.models import Environment


def test_get_identities_returns_bad_request_if_dynamo_is_not_enabled(
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


def test_get_identity(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    identity_uuid = identity_document["identity_uuid"]

    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment_api_key, identity_uuid],
    )
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    # When
    response = admin_client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["identity_uuid"] == identity_uuid
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )


def test_get_identity_returns_404_if_identity_does_not_exists(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment_api_key, "identity_uuid_that_does_not_exists"],
    )
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.side_effect = NotFound

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_identity(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    edge_identity_dynamo_wrapper_mock,
    identity_document,
):
    # Given
    identifier = identity_document["identifier"]
    composite_key = identity_document["composite_key"]
    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    edge_identity_dynamo_wrapper_mock.get_item.return_value = None

    # When
    response = admin_client.post(url, data={"identifier": identifier})

    # Then, test that get_item was called to verify that identity does not exists already
    edge_identity_dynamo_wrapper_mock.get_item.assert_called_with(composite_key)

    # Next, let verify that put item was called with correct args
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    assert args[0]["identifier"] == identifier
    assert args[0]["composite_key"] == composite_key

    # Finally, let's verify the response
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["identifier"] == identifier
    assert response.json()["identity_uuid"] is not None


def test_create_identity_returns_400_if_identity_already_exists(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    identifier = identity_document["identifier"]

    url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    edge_identity_dynamo_wrapper_mock.get_item.return_value = identity_document
    response = admin_client.post(url, data={"identifier": identifier})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_identity(
    admin_client: APIClient,
    dynamo_enabled_environment: int,
    environment_api_key: str,
    identity_document_without_fs: dict[str, Any],
    identity_document: dict[str, Any],
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    identity_overrides_v2: list[str],
) -> None:
    # Given
    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment_api_key, identity_uuid],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert not dynamodb_identity_wrapper.query_items(
        IndexName="identity_uuid-index",
        KeyConditionExpression=Key("identity_uuid").eq(identity_uuid),
    )["Count"]
    assert not list(
        dynamodb_wrapper_v2.query_iter_all_items(
            KeyConditionExpression=Key("environment_id").eq(
                str(dynamo_enabled_environment)
            )
        )
    )


def test_identity_list_pagination(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
):
    # Firstly, let's setup the data
    identity_item_key = {
        k: v
        for k, v in identity_document.items()
        if k in ["composite_key", "environment_api_key", "identifier"]
    }

    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    url = f"{base_url}?page_size=1"
    edge_identity_dynamo_wrapper_mock.get_all_items.side_effect = [
        {
            "Items": [identity_document],
            "Count": 1,
            "LastEvaluatedKey": identity_item_key,
        },
        {"Items": [identity_document], "Count": 1, "LastEvaluatedKey": None},
    ]

    response = admin_client.get(url)
    # Next, Test the response
    assert response.status_code == 200
    response = response.json()

    # Fetch the `last_evaluated_key` from the response since LastEvaluatedKey was part of the response from dynamodb
    last_evaluated_key = response["last_evaluated_key"]

    # Make the call using the `last_evaluated_key`
    url = f"{url}&last_evaluated_key={last_evaluated_key}"
    response = admin_client.get(url)

    # And verify that get_all_items was called with correct arguments
    edge_identity_dynamo_wrapper_mock.get_all_items.assert_called_with(
        environment_api_key, 1, identity_item_key
    )
    # And `last_evaluated_key` is now None
    assert response.status_code == 200
    assert response.json()["last_evaluated_key"] is None


def test_get_identities_list(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    url = f"{base_url}?page_size=9999"

    edge_identity_dynamo_wrapper_mock.get_all_items.return_value = {
        "Items": [identity_document],
        "Count": 1,
    }

    # When
    response = admin_client.get(url)
    assert (
        response.json()["results"][0]["identifier"] == identity_document["identifier"]
    )
    assert len(response.json()["results"]) == 1

    # Then
    assert response.status_code == status.HTTP_200_OK
    edge_identity_dynamo_wrapper_mock.get_all_items.assert_called_with(
        environment_api_key, 100, None
    )


def test_search_identities_without_exact_match(
    admin_client: APIClient,
    dynamo_enabled_environment: Environment,
    environment_api_key: str,
    identity_document: dict[str, Any],
    flagsmith_identities_table: Table,
):
    # Given
    identifier = identity_document["identifier"]

    flagsmith_identities_table.put_item(Item=identity_document)

    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )

    url = "%s?q=%s" % (base_url, identifier[:6])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["identifier"] == identifier


def test_search_for_identities_with_exact_match(
    admin_client: APIClient,
    dynamo_enabled_environment: Environment,
    environment_api_key: str,
    identity_document: dict[str, Any],
    flagsmith_identities_table: Table,
):
    # Given
    identifier = identity_document["identifier"]
    flagsmith_identities_table.put_item(Item=identity_document)

    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    url = "%s?%s" % (
        base_url,
        urllib.parse.urlencode({"q": f'"{identifier}"'}),
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["identifier"] == identifier


def test_search_for_identities_by_dashboard_alias_prefix(
    admin_client: APIClient,
    dynamo_enabled_environment: Environment,
    environment_api_key: str,
    identity_document: dict[str, Any],
    flagsmith_identities_table: Table,
) -> None:
    # Given
    identifier = identity_document["identifier"]

    # This test verifies a previous bug which meant that if any of the
    # leading characters to the search string were contained in the
    # `string `"dashboard_alias:"` then they would also be removed
    # and the search would fail.
    identity_document["dashboard_alias"] = "hans.gruber@example.com"
    search_string = "hans"

    flagsmith_identities_table.put_item(Item=identity_document)

    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    url = "%s?%s" % (
        base_url,
        urllib.parse.urlencode(
            {"q": f"{DASHBOARD_ALIAS_SEARCH_PREFIX}{search_string}"}
        ),
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["identifier"] == identifier


def test_search_for_identities_by_dashboard_alias_exact(
    admin_client: APIClient,
    dynamo_enabled_environment: Environment,
    environment_api_key: str,
    identity_document: dict[str, Any],
    flagsmith_identities_table: Table,
) -> None:
    # Given
    identifier = identity_document["identifier"]
    dashboard_alias = identity_document["dashboard_alias"]

    flagsmith_identities_table.put_item(Item=identity_document)

    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    url = "%s?%s" % (
        base_url,
        urllib.parse.urlencode(
            {"q": f'{DASHBOARD_ALIAS_SEARCH_PREFIX}"{dashboard_alias}"'}
        ),
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["identifier"] == identifier


def test_search_for_identities_by_dashboard_alias_casts_search_to_lower(
    admin_client: APIClient,
    dynamo_enabled_environment: Environment,
    environment_api_key: str,
    identity_document: dict[str, Any],
    flagsmith_identities_table: Table,
) -> None:
    # Given
    identifier = identity_document["identifier"]
    dashboard_alias = identity_document["dashboard_alias"]

    flagsmith_identities_table.put_item(Item=identity_document)

    base_url = reverse(
        "api-v1:environments:environment-edge-identities-list",
        args=[environment_api_key],
    )
    url = "%s?%s" % (
        base_url,
        urllib.parse.urlencode(
            {"q": f'{DASHBOARD_ALIAS_SEARCH_PREFIX}"{dashboard_alias.upper()}"'}
        ),
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["identifier"] == identifier


def test_update_edge_identity(
    admin_client_new: APIClient,
    dynamo_enabled_environment: Environment,
    environment_api_key: str,
    identity_document: dict[str, Any],
    flagsmith_identities_table: Table,
) -> None:
    # Given
    identity_uuid = identity_document["identity_uuid"]
    composite_key = identity_document["composite_key"]

    input_dashboard_alias = "New-Dashboard-Alias"
    expected_dashboard_alias = input_dashboard_alias.lower()

    flagsmith_identities_table.put_item(Item=identity_document)

    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment_api_key, identity_uuid],
    )

    # When
    response = admin_client_new.patch(
        url, data={"dashboard_alias": input_dashboard_alias}
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "dashboard_alias": expected_dashboard_alias,
        "identifier": identity_document["identifier"],
        "identity_uuid": identity_uuid,
    }

    # Let's also validate that the fields are the same between the original document,
    # and from the updated database, apart from the dashboard_alias which should have
    # been updated as expected.
    identity_from_db = flagsmith_identities_table.get_item(
        Key={"composite_key": composite_key}
    )["Item"]
    assert {
        **identity_document,
        "dashboard_alias": expected_dashboard_alias,
    } == identity_from_db


def test_edge_identities_traits_list(
    admin_client,
    environment_api_key,
    identity_document,
    identity_traits,
    dynamo_enabled_environment,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )

    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:environment-edge-identities-get-traits",
        args=[environment_api_key, identity_uuid],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == identity_traits

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )


def test_edge_identities_trait_delete(
    admin_client,
    environment_api_key,
    dynamo_enabled_environment,
    identity_document,
    identity_traits,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    identity_uuid = identity_document["identity_uuid"]
    trait_key = identity_traits[0]["trait_key"]
    url = reverse(
        "api-v1:environments:environment-edge-identities-update-traits",
        args=[environment_api_key, identity_uuid],
    )
    data = {"trait_key": trait_key, "trait_value": None}

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    # Next, let's verify that deleted trait
    # is not part of identity dict that we put
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    assert not list(
        filter(
            lambda trait: trait["trait_key"] == trait_key,
            args[0]["identity_traits"],
        )
    )


def test_edge_identities_create_trait(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    identity_uuid = identity_document["identity_uuid"]
    url = reverse(
        "api-v1:environments:environment-edge-identities-update-traits",
        args=[environment_api_key, identity_uuid],
    )
    trait_key = "new_trait_key"
    data = {"trait_key": trait_key, "trait_value": "new_trait_value"}

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["trait_key"] == trait_key

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    # Next, let's verify that new trait
    # is part of identity dict that we put
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    assert list(
        filter(
            lambda trait: trait["trait_key"] == trait_key,
            args[0]["identity_traits"],
        )
    )


def test_edge_identities_update_trait(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    identity_traits,
    edge_identity_dynamo_wrapper_mock,
    mocker,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    identity_uuid = identity_document["identity_uuid"]
    trait_key = identity_traits[0]["trait_key"]
    url = reverse(
        "api-v1:environments:environment-edge-identities-update-traits",
        args=[environment_api_key, identity_uuid],
    )
    updated_trait_value = "updated_trait_value"
    data = {"trait_key": trait_key, "trait_value": updated_trait_value}

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["trait_key"] == trait_key
    assert response.json()["trait_value"] == updated_trait_value
    # and
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    # Next, let's verify that updated trait value
    # is part of identity dict that we put
    name, args, _ = edge_identity_dynamo_wrapper_mock.mock_calls[1]
    assert name == "put_item"
    assert list(
        filter(
            lambda trait: trait["trait_key"] == trait_key
            and trait["trait_value"] == updated_trait_value,
            args[0]["identity_traits"],
        )
    )


def test_edge_identities_update_trait_with_same_value(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    identity_traits,
    edge_identity_dynamo_wrapper_mock,
    mocker,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    identity_uuid = identity_document["identity_uuid"]
    trait_key = identity_traits[0]["trait_key"]
    trait_value = identity_traits[0]["trait_value"]
    url = reverse(
        "api-v1:environments:environment-edge-identities-update-traits",
        args=[environment_api_key, identity_uuid],
    )
    data = {"trait_key": trait_key, "trait_value": trait_value}

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_200_OK

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    edge_identity_dynamo_wrapper_mock.put_item.assert_not_called()


def test_edge_identities_update_traits_returns_400_if_persist_trait_data_is_false(
    admin_client,
    dynamo_enabled_environment,
    environment_api_key,
    identity_document,
    identity_traits,
    edge_identity_dynamo_wrapper_mock,
    organisation_with_persist_trait_data_disabled,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document
    )
    identity_uuid = identity_document["identity_uuid"]
    trait_key = identity_traits[0]["trait_key"]

    url = reverse(
        "api-v1:environments:environment-edge-identities-update-traits",
        args=[environment_api_key, identity_uuid],
    )
    updated_trait_value = "updated_trait_value"
    data = {"trait_key": trait_key, "trait_value": updated_trait_value}

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
