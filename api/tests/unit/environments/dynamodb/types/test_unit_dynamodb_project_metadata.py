from datetime import datetime
from decimal import Decimal

import pytest
from mypy_boto3_dynamodb.service_resource import Table
from pytest_mock import MockerFixture

from environments.dynamodb.types import (
    DynamoProjectMetadata,
    ProjectIdentityMigrationStatus,
)


def test_get_or_new_returns_instance_with_default_values_if_document_does_not_exists(  # type: ignore[no-untyped-def]
    mocker,
):
    # Given
    project_id = 1
    mocked_dynamo_table = mocker.patch(
        "environments.dynamodb.types.project_metadata_table"
    )
    mocked_dynamo_table.get_item.return_value = {
        "ResponseMetadata": {"some_key": "some_value"}
    }

    # When
    project_metadata = DynamoProjectMetadata.get_or_new(project_id)
    # Then
    assert project_metadata.id == project_id
    assert project_metadata.migration_start_time is None
    assert project_metadata.migration_end_time is None
    mocked_dynamo_table.get_item.assert_called_with(Key={"id": project_id})


def test_get_or_new_returns_instance_with_document_data_if_document_does_exists(mocker):  # type: ignore[no-untyped-def]  # noqa: E501
    # Given
    project_id = 1
    migration_start_time = datetime.now().isoformat()
    mocked_dynamo_table = mocker.patch(
        "environments.dynamodb.types.project_metadata_table"
    )
    mocked_dynamo_table.get_item.return_value = {
        "ResponseMetadata": {"some_key": "some_value"},
        "Item": {
            "id": Decimal(project_id),
            "migration_start_time": migration_start_time,
        },
    }
    # When
    project_metadata = DynamoProjectMetadata.get_or_new(project_id)

    # Then
    assert project_metadata.id == project_id
    assert project_metadata.migration_start_time == migration_start_time
    assert project_metadata.migration_end_time is None

    mocked_dynamo_table.get_item.assert_called_with(Key={"id": project_id})


def test_start_identity_migration_calls_put_item_with_correct_arguments(mocker):  # type: ignore[no-untyped-def]
    # Given
    project_id = 1

    migration_start_time = datetime.now()
    mocked_dynamo_table = mocker.patch(
        "environments.dynamodb.types.project_metadata_table"
    )
    mocked_dynamo_table.get_item.return_value = {
        "ResponseMetadata": {"some_key": "some_value"}
    }
    mocked_datetime = mocker.patch("environments.dynamodb.types.datetime")
    mocked_datetime.now.return_value = migration_start_time

    project_metadata = DynamoProjectMetadata.get_or_new(project_id)

    # When
    project_metadata.start_identity_migration()  # type: ignore[no-untyped-call]
    # Then
    mocked_dynamo_table.get_item.assert_called_with(Key={"id": project_id})
    mocked_dynamo_table.put_item.assert_called_with(
        Item={
            "id": project_id,
            "migration_end_time": None,
            "migration_start_time": migration_start_time.isoformat(),
            "triggered_at": None,
        }
    )


@pytest.mark.parametrize(
    "instance, status",
    (
        (
            DynamoProjectMetadata(id=1),
            ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED,
        ),
        (
            DynamoProjectMetadata(id=1, triggered_at=datetime.now().isoformat()),
            ProjectIdentityMigrationStatus.MIGRATION_SCHEDULED,
        ),
        (
            DynamoProjectMetadata(
                id=1, migration_start_time=datetime.now().isoformat()
            ),
            ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS,
        ),
        (
            DynamoProjectMetadata(
                id=1,
                migration_start_time=datetime.now().isoformat(),
                migration_end_time=datetime.now().isoformat(),
            ),
            ProjectIdentityMigrationStatus.MIGRATION_COMPLETED,
        ),
    ),
)
def test_identity_migration_status(instance, status):  # type: ignore[no-untyped-def]
    assert instance.identity_migration_status == status


def test_finish_identity_migration_calls_put_item_with_correct_arguments(  # type: ignore[no-untyped-def]
    mocker,
):
    # Given
    project_id = 1
    migration_start_time = datetime.now().isoformat()

    migration_end_time = datetime.now()
    mocked_dynamo_table = mocker.patch(
        "environments.dynamodb.types.project_metadata_table"
    )
    mocked_datetime = mocker.patch("environments.dynamodb.types.datetime")
    mocked_datetime.now.return_value = migration_end_time

    project_metadata = DynamoProjectMetadata(
        id=project_id, migration_start_time=migration_start_time
    )

    # When
    project_metadata.finish_identity_migration()  # type: ignore[no-untyped-call]

    # Then
    mocked_dynamo_table.put_item.assert_called_with(
        Item={
            "id": project_id,
            "migration_start_time": migration_start_time,
            "migration_end_time": migration_end_time.isoformat(),
            "triggered_at": None,
        }
    )


def test_delete__removes_project_metadata_document_from_dynamodb(  # type: ignore[no-untyped-def]
    flagsmith_project_metadata_table: Table, mocker: MockerFixture
):
    # Given
    first_project_id = 1
    mocker.patch(
        "environments.dynamodb.types.project_metadata_table",
        flagsmith_project_metadata_table,
    )
    flagsmith_project_metadata_table.put_item(Item={"id": first_project_id})
    # Let's add another item to make sure that only the correct item is deleted
    second_project_id = 2
    flagsmith_project_metadata_table.put_item(Item={"id": second_project_id})

    project_metadata = DynamoProjectMetadata.get_or_new(first_project_id)

    # When
    project_metadata.delete()  # type: ignore[no-untyped-call]

    # Then
    assert flagsmith_project_metadata_table.scan()["Count"] == 1
    assert (
        flagsmith_project_metadata_table.scan()["Items"][0]["id"] == second_project_id
    )
