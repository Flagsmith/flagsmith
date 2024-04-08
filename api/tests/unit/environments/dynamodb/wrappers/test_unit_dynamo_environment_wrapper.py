import pytest
from django.core.exceptions import ObjectDoesNotExist
from mypy_boto3_dynamodb.service_resource import Table
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.dynamodb import DynamoEnvironmentWrapper
from environments.models import Environment
from util.mappers import map_environment_to_environment_document


def test_write_environments_calls_internal_methods_with_correct_arguments(
    mocker, project, environment
):
    # Given
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")

    expected_environment_document = map_environment_to_environment_document(environment)
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


def test_get_environment_uses_dax_if_enabled(
    mocker: MockerFixture, settings: SettingsWrapper
):
    # Given
    settings.DAX_ENDPOINT = "dax://test"
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    expected_document = {"key": "value"}
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")
    mocked_dax_table = mocker.patch.object(dynamo_environment_wrapper, "_dax_table")

    mocked_dax_table.get_item.return_value = {"Item": expected_document}
    api_key = "test_key"

    # When
    returned_item = dynamo_environment_wrapper.get_environment(api_key)

    # Then
    mocked_dax_table.get_item.assert_called_with(Key={"api_key": api_key})
    assert returned_item == expected_document
    mocked_dynamo_table.get_item.assert_not_called()


def test_get_environment_calls_dynamo_get_item_with_correct_arguments(mocker):
    # Given
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    expected_document = {"key": "value"}
    api_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")
    mocked_dynamo_table.get_item.return_value = {"Item": expected_document}

    # When
    returned_item = dynamo_environment_wrapper.get_environment(api_key)

    # Then
    mocked_dynamo_table.get_item.assert_called_with(Key={"api_key": api_key})
    assert returned_item == expected_document


def test_get_environment_raises_object_does_not_exists_if_get_item_does_not_return_any_item(
    mocker,
):
    # Given
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    api_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")
    mocked_dynamo_table.get_item.return_value = {}

    # Then
    with pytest.raises(ObjectDoesNotExist):
        dynamo_environment_wrapper.get_environment(api_key)


def test_delete_environment__removes_environment_document_from_dynamodb(
    dynamo_enabled_project_environment_one_document: dict,
    dynamo_environment_wrapper: DynamoEnvironmentWrapper,
    flagsmith_environment_table: Table,
):
    # Given
    api_key = dynamo_enabled_project_environment_one_document["api_key"]
    assert flagsmith_environment_table.scan()["Count"] == 1

    # When
    dynamo_environment_wrapper.delete_environment(api_key)

    # Then
    assert flagsmith_environment_table.scan()["Count"] == 0


def test_delete_environment__calls_dax_if_configured(
    dynamo_enabled_project_environment_one_document: dict,
    dynamo_environment_wrapper: DynamoEnvironmentWrapper,
    flagsmith_environment_table: Table,
    settings: SettingsWrapper,
    mocker: MockerFixture,
):
    # Given
    settings.DAX_ENDPOINT = "dax://test"
    api_key = dynamo_enabled_project_environment_one_document["api_key"]
    mocked_dax_table = mocker.patch.object(dynamo_environment_wrapper, "_dax_table")

    # When
    dynamo_environment_wrapper.delete_environment(api_key)

    # Then
    mocked_dax_table.delete_item.assert_called_with(Key={"api_key": api_key})

    # document should still exists because we mocked the dax call
    assert flagsmith_environment_table.scan()["Count"] == 1
