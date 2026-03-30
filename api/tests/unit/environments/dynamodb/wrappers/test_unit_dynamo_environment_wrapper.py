import pytest
from boto3.dynamodb.types import Binary
from common.test_tools import AssertMetricFixture
from django.core.exceptions import ObjectDoesNotExist
from mypy_boto3_dynamodb.service_resource import Table
from pytest_structlog import StructuredLogCapture

from environments.dynamodb import DynamoEnvironmentWrapper
from environments.models import Environment
from tests.types import EnableFeaturesFixture
from util.mappers import map_environment_to_environment_document


def test_write_environments__valid_environments__calls_batch_writer_correctly(  # type: ignore[no-untyped-def]
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


def test_write_environments__compress_dynamo_documents_enabled__writes_compressed(
    environment: Environment,
    dynamo_environment_wrapper: DynamoEnvironmentWrapper,
    flagsmith_environment_table: Table,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("compress_dynamo_documents")

    # When
    dynamo_environment_wrapper.write_environments([environment])

    # Then
    results = flagsmith_environment_table.scan()["Items"]
    assert len(results) == 1
    assert results[0]["compressed"] is True
    assert isinstance(results[0]["project"], Binary)
    assert isinstance(results[0]["feature_states"], Binary)


def test_write_environments__compress_dynamo_documents_enabled__observes_metrics(
    environment: Environment,
    dynamo_environment_wrapper: DynamoEnvironmentWrapper,
    flagsmith_environment_table: Table,
    enable_features: EnableFeaturesFixture,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given
    enable_features("compress_dynamo_documents")

    # When
    dynamo_environment_wrapper.write_environments([environment])

    # Then
    assert_metric(
        name="flagsmith_dynamo_environment_document_size_bytes_count",
        labels={"table": flagsmith_environment_table.name, "compressed": "true"},
        value=1.0,
    )
    assert_metric(
        name="flagsmith_dynamo_environment_document_compression_ratio_count",
        labels={"table": flagsmith_environment_table.name},
        value=1.0,
    )


def test_write_environments__uncompressed__observes_size_metric(
    environment: Environment,
    dynamo_environment_wrapper: DynamoEnvironmentWrapper,
    flagsmith_environment_table: Table,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given / When
    dynamo_environment_wrapper.write_environments([environment])

    # Then
    assert_metric(
        name="flagsmith_dynamo_environment_document_size_bytes_count",
        labels={"table": flagsmith_environment_table.name, "compressed": "false"},
        value=1.0,
    )


def test_write_environments__compress_dynamo_documents_enabled__logs_expected(
    environment: Environment,
    dynamo_environment_wrapper: DynamoEnvironmentWrapper,
    flagsmith_environment_table: Table,
    enable_features: EnableFeaturesFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    enable_features("compress_dynamo_documents")

    # When
    dynamo_environment_wrapper.write_environments([environment])

    # Then
    assert log.events == [
        {
            "environment_api_key": environment.api_key,
            "environment_id": environment.id,
            "event": "environment-document-compressed",
            "level": "info",
        },
    ]


def test_get_item__valid_api_key__returns_expected_document(mocker):  # type: ignore[no-untyped-def]
    # Given
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    expected_document = {"key": "value"}
    api_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")
    mocked_dynamo_table.get_item.return_value = {"Item": expected_document}

    # When
    returned_item = dynamo_environment_wrapper.get_item(api_key)

    # Then
    mocked_dynamo_table.get_item.assert_called_with(Key={"api_key": api_key})
    assert returned_item == expected_document


def test_get_item__no_item_returned__raises_object_does_not_exist(  # type: ignore[no-untyped-def]
    mocker,
):
    # Given
    dynamo_environment_wrapper = DynamoEnvironmentWrapper()
    api_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_environment_wrapper, "_table")
    mocked_dynamo_table.get_item.return_value = {}

    # When / Then
    with pytest.raises(ObjectDoesNotExist):
        dynamo_environment_wrapper.get_item(api_key)


def test_delete_environment__existing_document__removes_from_dynamodb(  # type: ignore[no-untyped-def]
    dynamo_enabled_project_environment_one_document: dict,  # type: ignore[type-arg]
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
