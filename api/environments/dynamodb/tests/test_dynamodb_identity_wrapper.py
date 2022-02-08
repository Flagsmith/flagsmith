from boto3.dynamodb.conditions import Key
from flag_engine.django_transform.document_builders import (
    build_identity_document,
)

from environments.dynamodb import DynamoIdentityWrapper


def test_get_item_from_uuid_calls_query_with_correct_argument(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    environment_key = "environment_key"
    identity_uuid = "test_uuid"

    # When
    dynamo_identity_wrapper.get_item_from_uuid(environment_key, identity_uuid)
    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="identity_uuid-index",
        Limit=1,
        KeyConditionExpression=Key("identity_uuid").eq(identity_uuid),
    )


def test_delete_item_calls_dynamo_delete_item_with_correct_arguments(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    composite_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.delete_item(composite_key)

    # Then
    mocked_dynamo_table.delete_item.assert_called_with(
        Key={"composite_key": composite_key}
    )


def test_get_item_calls_dynamo_get_item_with_correct_arguments(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    composite_key = "test_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.get_item(composite_key)

    # Then
    mocked_dynamo_table.get_item.assert_called_with(
        Key={"composite_key": composite_key}
    )


def test_get_all_items_without_start_key_calls_query_with_correct_arguments(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    environment_key = "environment_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")

    # When
    dynamo_identity_wrapper.get_all_items(environment_key, 999)

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key),
    )


def test_get_all_items_with_start_key_calls_query_with_correct_arguments(mocker):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    environment_key = "environment_key"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    start_key = {"key": "value"}

    # When
    dynamo_identity_wrapper.get_all_items(environment_key, 999, start_key)

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key),
        ExclusiveStartKey=start_key,
    )


def test_search_items_with_identifier_calls_query_with_correct_arguments(mocker):
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    environment_key = "environment_key"
    identifier = "test_user"
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    start_key = {"key": "value"}
    search_function = lambda x: Key("identifier").eq(x)  # noqa: E731

    # When
    dynamo_identity_wrapper.search_items_with_identifier(
        environment_key, identifier, search_function, 999, start_key
    )

    # Then
    mocked_dynamo_table.query.assert_called_with(
        IndexName="environment_api_key-identifier-index",
        Limit=999,
        KeyConditionExpression=Key("environment_api_key").eq(environment_key)
        & search_function(identifier),
        ExclusiveStartKey=start_key,
    )


def test_migrate_identities_calls_internal_methods_with_correct_arguments(
    mocker, project, identity
):
    # Given
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    mocked_dynamo_table = mocker.patch.object(dynamo_identity_wrapper, "_table")
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.dynamodb_wrapper.DynamoProjectMetadata"
    )

    expected_identity_document = build_identity_document(identity)
    # When
    dynamo_identity_wrapper.migrate_identities(project.id)

    # Then
    mocked_dynamo_table.batch_writer.assert_called_with()

    mocked_put_item = (
        mocked_dynamo_table.batch_writer.return_value.__enter__.return_value.put_item
    )
    _, kwargs = mocked_put_item.call_args
    actual_identity_document = kwargs["Item"]

    # Remove identity_uuid from the document since it will be different
    actual_identity_document.pop("identity_uuid")
    expected_identity_document.pop("identity_uuid")

    assert actual_identity_document == expected_identity_document

    # Make sure that Project Metadata Wrapper was called correctly
    mocked_project_metadata.get_or_new.assert_called_with(project.id)
    # and `is_identity_migration_done` was updated successfully
    assert (
        mocked_project_metadata.get_or_new.return_value.is_identity_migration_done
        is True
    )
    mocked_project_metadata.get_or_new.return_value.save.assert_called_with()


def test_is_migration_done_calls_dynamo_project_metadata_wrapper_with_correct_arguments(
    mocker,
):
    # Given
    project_id = 1
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.dynamodb_wrapper.DynamoProjectMetadata"
    )
    dynamo_identity_wrapper = DynamoIdentityWrapper()

    # When

    result = dynamo_identity_wrapper.is_migration_done(project_id)
    # Then

    mocked_project_metadata.get_or_new.assert_called_with(project_id)
    assert (
        result
        == mocked_project_metadata.get_or_new.return_value.is_identity_migration_done
    )
