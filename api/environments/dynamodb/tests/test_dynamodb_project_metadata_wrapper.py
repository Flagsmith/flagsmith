from decimal import Decimal

from environments.dynamodb.dynamodb_wrapper import DynamoProjectMetadataWrapper
from environments.dynamodb.types import DynamoProjectMetadata


def test_is_identity_migration_done_return_false_if_dcoument_does_not_exists(mocker):
    # Given
    project_id = 1
    wrapper = DynamoProjectMetadataWrapper(project_id)

    mocked_dynamo_table = mocker.patch.object(wrapper, "_table")
    mocked_get_item = mocker.MagicMock(
        return_value={"ResponseMetadata": {"some_key": "some_value"}}
    )

    mocked_dynamo_table.get_item = mocked_get_item

    # When
    result = wrapper.is_identity_migration_done

    # Then
    assert result is False
    mocked_get_item.assert_called_with(Key={"id": project_id})


def test_is_identity_migration_done_return_correct_value_if_dcoument_exists(mocker):
    # Given
    project_id = 1
    wrapper = DynamoProjectMetadataWrapper(project_id)

    mocked_dynamo_table = mocker.patch.object(wrapper, "_table")
    expected_is_migration_done = True
    mocked_get_item = mocker.MagicMock(
        return_value={
            "ResponseMetadata": {"some_key": "some_value"},
            "Item": {
                "id": Decimal("1"),
                "is_migration_done": expected_is_migration_done,
            },
        }
    )
    mocked_dynamo_table.get_item = mocked_get_item

    # When
    actual_is_migration_done = wrapper.is_identity_migration_done

    # Then
    assert actual_is_migration_done is expected_is_migration_done
    mocked_get_item.assert_called_with(Key={"id": project_id})


def test_mark_identity_migration_as_done_calls_put_item_with_correct_arguments_if_document_exsits(
    mocker,
):
    # Given
    project_id = 1
    wrapper = DynamoProjectMetadataWrapper(project_id)

    mocked_dynamo_table = mocker.patch.object(wrapper, "_table")
    mocked_get_item = mocker.MagicMock(
        return_value={
            "ResponseMetadata": {"some_key": "some_value"},
            "Item": {
                "id": Decimal("1"),
                "is_migration_done": True,
            },
        }
    )
    mocked_dynamo_table.get_item = mocked_get_item
    # When
    wrapper.mark_identity_migration_as_done()

    # Then
    mocked_get_item.assert_called_with(Key={"id": project_id})
    mocked_dynamo_table.put_item.assert_called_with(
        Item={"id": project_id, "is_migration_done": True}
    )


def test_mark_identity_migration_as_done_calls_put_item_with_correct_arguments_if_document_does_not_exsits(
    mocker,
):
    # Given
    project_id = 1
    wrapper = DynamoProjectMetadataWrapper(project_id)

    mocked_dynamo_table = mocker.patch.object(wrapper, "_table")
    mocked_get_item = mocker.MagicMock(
        return_value={
            "ResponseMetadata": {"some_key": "some_value"},
        }
    )
    mocked_dynamo_table.get_item = mocked_get_item
    # When
    wrapper.mark_identity_migration_as_done()

    # Then
    mocked_get_item.assert_called_with(Key={"id": project_id})
    mocked_dynamo_table.put_item.assert_called_with(
        Item={"id": project_id, "is_migration_done": True}
    )


def test_get_instance_or_none_returns_none_if_document_does_not_exists(mocker):
    # Given
    project_id = 1
    wrapper = DynamoProjectMetadataWrapper(project_id)

    mocked_dynamo_table = mocker.patch.object(wrapper, "_table")
    mocked_get_item = mocker.MagicMock(
        return_value={
            "ResponseMetadata": {"some_key": "some_value"},
        }
    )
    mocked_dynamo_table.get_item = mocked_get_item
    # When
    instance = wrapper._get_instance_or_none()
    assert instance is None
    mocked_get_item.assert_called_with(Key={"id": project_id})


def test_get_instance_or_none_returns_dynamo_project_metadata_instance_if_document_exists(
    mocker,
):
    # Given
    project_id = 1
    wrapper = DynamoProjectMetadataWrapper(project_id)

    expected_is_migration_done = True
    expected_project_metadata_id = 10
    mocked_get_item = mocker.MagicMock(
        return_value={
            "ResponseMetadata": {"some_key": "some_value"},
            "Item": {
                "id": Decimal(f"{expected_project_metadata_id}"),
                "is_migration_done": expected_is_migration_done,
            },
        }
    )

    mocked_dynamo_table = mocker.patch.object(wrapper, "_table")
    mocked_dynamo_table.get_item = mocked_get_item
    expected_instance = DynamoProjectMetadata(
        id=expected_project_metadata_id, is_migration_done=expected_is_migration_done
    )

    # When
    actual_instance = wrapper._get_instance_or_none()
    assert actual_instance == expected_instance
    mocked_get_item.assert_called_with(Key={"id": project_id})
