from decimal import Decimal

from environments.dynamodb.types import DynamoProjectMetadata


def test_get_or_new_returns_instnace_with_default_values_if_document_does_not_exists(
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
    assert project_metadata.is_identity_migration_done is False
    mocked_dynamo_table.get_item.assert_called_with(Key={"id": project_id})


def test_get_or_new_returns_instnace_with_document_data_if_document_does_exists(mocker):
    # Given
    project_id = 1

    expected_is_migration_done = True
    mocked_dynamo_table = mocker.patch(
        "environments.dynamodb.types.project_metadata_table"
    )
    mocked_dynamo_table.get_item.return_value = {
        "ResponseMetadata": {"some_key": "some_value"},
        "Item": {
            "id": Decimal(project_id),
            "is_identity_migration_done": expected_is_migration_done,
        },
    }

    # When
    project_metadata = DynamoProjectMetadata.get_or_new(project_id)

    # Then
    assert project_metadata.id == project_id
    assert project_metadata.is_identity_migration_done is expected_is_migration_done
    mocked_dynamo_table.get_item.assert_called_with(Key={"id": project_id})


def test_save_calls_put_item_with_correct_arguments(mocker):
    # Given
    project_id = 1
    mocked_dynamo_table = mocker.patch(
        "environments.dynamodb.types.project_metadata_table"
    )
    mocked_dynamo_table.get_item.return_value = {
        "ResponseMetadata": {"some_key": "some_value"}
    }
    project_metadata = DynamoProjectMetadata.get_or_new(project_id)

    # When
    project_metadata.is_identity_migration_done = True
    project_metadata.save()

    # Then
    mocked_dynamo_table.get_item.assert_called_with(Key={"id": project_id})
    mocked_dynamo_table.put_item.assert_called_with(
        Item={"id": project_id, "is_identity_migration_done": True}
    )
