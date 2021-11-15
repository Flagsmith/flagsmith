import base64
import json

from rest_framework.utils.urls import replace_query_param

from app.pagination import IdentityPagination


def test_identity_pagination_set_pagination_state_dynamodb(rf):
    # Given
    paginator = IdentityPagination()
    query_params = {"last_evaluated_key": "some_random_key"}
    request = rf.get("test", query_params)
    dynamo_queryset = {"Count": 10, "LastEvaluatedKey": {"api_key": "test"}}

    # When
    paginator.set_pagination_state_dynamo(dynamo_queryset, request)

    # Then
    assert paginator.last_evaluated_key == base64.b64encode(
        json.dumps(dynamo_queryset["LastEvaluatedKey"]).encode()
    )
    assert paginator.dynamodb_count == dynamo_queryset["Count"]
    assert paginator.previous_last_evaluated_key == query_params["last_evaluated_key"]


def test_identity_pagination_next_link_dynamodb(rf):
    # Given
    paginator = IdentityPagination()
    request = rf.get("test")
    last_evaluate_key = base64.b64encode(json.dumps({"api_key": "test"}).encode())

    # update the instance state
    paginator.request = request
    paginator.last_evaluated_key = last_evaluate_key

    # When
    next_url = paginator.next_link_dynamo()

    # Then
    assert next_url == replace_query_param(
        request.build_absolute_uri(), "last_evaluated_key", last_evaluate_key
    )


def test_identity_pagination_previous_link_dynamodb(rf):
    # Given
    paginator = IdentityPagination()
    request = rf.get("test")
    previous_last_evaluated_key = base64.b64encode(b"some_test_key")

    # update the instance state
    paginator.request = request
    paginator.previous_last_evaluated_key = previous_last_evaluated_key

    # When
    previous_url = paginator.previous_link_dynamo()

    # Then
    assert previous_url == replace_query_param(
        request.build_absolute_uri(), "last_evaluated_key", previous_last_evaluated_key
    )


def test_identity_pagination_get_paginated_response_dynamo(rf):
    # Given
    paginator = IdentityPagination()
    query_params = {"last_evaluated_key": "some_random_key"}
    request = rf.get("test", query_params)
    dynamo_queryset = {"Count": 10, "LastEvaluatedKey": {"api_key": "test"}}
    data = {"key": "value"}
    paginator.set_pagination_state_dynamo(dynamo_queryset, request)

    # When
    response = paginator.get_paginated_response_dynamo(data)

    # Then
    assert set(response.data.keys()) == {"count", "results", "previous", "next"}
    assert response.data["count"] == dynamo_queryset["Count"]
    assert response.data["results"] == data
