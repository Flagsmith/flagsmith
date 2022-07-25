from unittest.mock import MagicMock

import pytest
from core.request_origin import RequestOrigin
from django.db.models import Q
from pytest_django.asserts import assertQuerysetEqual as assert_queryset_equal

from environments.models import Environment


@pytest.mark.parametrize(
    "allow_client_traits, request_origin, expected_result",
    (
        (True, RequestOrigin.CLIENT, True),
        (True, RequestOrigin.SERVER, True),
        (False, RequestOrigin.CLIENT, False),
        (False, RequestOrigin.SERVER, True),
    ),
)
def test_environment_trait_persistence_allowed(
    allow_client_traits, request_origin, expected_result
):
    request = MagicMock(originated_from=request_origin)
    assert (
        Environment(allow_client_traits=allow_client_traits).trait_persistence_allowed(
            request
        )
        == expected_result
    )


def test_write_environments_to_dynamodb_with_environment(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environments_to_dynamodb(
        Q(id=dynamo_enabled_project_environment_one.id)
    )

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0],
        Environment.objects.filter(id=dynamo_enabled_project_environment_one.id),
    )


def test_write_environments_to_dynamodb_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    dynamo_enabled_project_environment_two,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environments_to_dynamodb(Q(project=dynamo_enabled_project))

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0], Environment.objects.filter(project=dynamo_enabled_project)
    )


def test_write_environments_to_dynamodb_with_environment_and_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environments_to_dynamodb(
        Q(id=dynamo_enabled_project_environment_one.id)
    )

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0],
        Environment.objects.filter(id=dynamo_enabled_project_environment_one.id),
    )
