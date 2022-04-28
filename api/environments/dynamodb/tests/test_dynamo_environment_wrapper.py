import pytest
from django.core.exceptions import ObjectDoesNotExist
from flag_engine.api.document_builders import build_environment_document

from environments.dynamodb import DynamoEnvironmentWrapper
from environments.models import Environment


def test_write_environments_calls_internal_methods_with_correct_arguments(
    mocker, project, environment
):
    # Given
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")

    expected_environment_document = build_environment_document(environment)
    environments = Environment.objects.filter(id=environment.id)

    # When
    dynamo_environment_wrapper.write_environments(environments)

    # Then
    mocked_dynamo_table.batch_writer.assert_called_with()

    mocked_put_item = (
        mocked_dynamo_table.batch_writer.return_value.__enter__.return_value.put_item
    )
    _, kwargs = mocked_put_item.call_args
    actual_environment_document = kwargs["Item"]

    assert actual_environment_document == expected_environment_document


def test_get_item_calls_dynamo_get_item_with_correct_arguments(mocker):
    # Given
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    expected_document = {"key": "value"}
    api_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")
    mocked_dynamo_table.get_item.return_value = {"Item": expected_document}

    # When
    retunred_item = dynamo_environment_wrapper.get_item(api_key)

    # Then
    mocked_dynamo_table.get_item.assert_called_with(Key={"api_key": api_key})
    assert retunred_item == expected_document


def test_get_item_raises_object_does_not_exists_if_get_item_does_not_return_any_item(
    mocker,
):
    # Given
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    api_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")
    mocked_dynamo_table.get_item.return_value = {}

    # Then
    with pytest.raises(ObjectDoesNotExist):
        dynamo_environment_wrapper.get_item(api_key)
