from datetime import datetime

from flag_engine.django_transform.document_builders import (
    build_identity_document,
)

from environments.dynamodb.migrator import IdentityMigrator
from environments.dynamodb.types import (
    DynamoProjectMetadata,
    ProjectIdentityMigrationStatus,
)


def test_migrate_identities_calls_internal_methods_with_correct_arguments(
    mocker, project, identity
):
    # Given
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.migrator.DynamoProjectMetadata"
    )
    mocked_project_metadata_instance = mocker.MagicMock(spec=DynamoProjectMetadata)
    mocked_project_metadata_instance.id = project.id
    mocked_project_metadata.get_or_new.return_value = mocked_project_metadata_instance
    mocked_dynamo_table = mocker.MagicMock()
    dynamo_identity_wrapper = mocker.patch(
        "environments.dynamodb.migrator.DynamoIdentityWrapper"
    )
    dynamo_identity_wrapper.return_value._table = mocked_dynamo_table
    expected_identity_document = build_identity_document(identity)

    identity_migrator = IdentityMigrator(project.id)

    # When
    identity_migrator.migrate()

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
    mocked_project_metadata_instance.start_identity_migration.assert_called_once_with()
    mocked_project_metadata_instance.finish_identity_migration.assert_called_once_with()


def test_is_migration_done_returns_true_if_migration_is_completed(
    mocker,
):
    # Given
    project_id = 1
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.migrator.DynamoProjectMetadata"
    )
    mocked_project_metadata_instance = mocker.MagicMock(
        spec=DynamoProjectMetadata,
        migration_start_time=datetime.now().isoformat(),
        migration_end_time=datetime.now().isoformat(),
    )

    mocked_project_metadata.get_or_new.return_value = mocked_project_metadata_instance

    identity_migrator = IdentityMigrator(project_id)

    # Then
    assert identity_migrator.is_migration_done is True
    mocked_project_metadata.get_or_new.assert_called_with(project_id)


def test_can_migrate_returns_true_if_migration_was_not_done(
    mocker,
):
    # Given
    project_id = 1
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.migrator.DynamoProjectMetadata"
    )
    mocked_project_metadata_instance = mocker.MagicMock(
        spec=DynamoProjectMetadata,
        migration_start_time=None,
        migration_end_time=None,
    )

    mocked_project_metadata.get_or_new.return_value = mocked_project_metadata_instance

    identity_migrator = IdentityMigrator(project_id)

    # Then
    assert identity_migrator.can_migrate is True

    mocked_project_metadata.get_or_new.assert_called_with(project_id)


def test_get_migration_status_returns_correct_migraion_status_for_in_progress_migration(
    mocker,
):
    # Given
    project_id = 1
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.migrator.DynamoProjectMetadata"
    )
    mocked_project_metadata_instance = mocker.MagicMock(
        spec=DynamoProjectMetadata,
        migration_start_time=datetime.now().isoformat(),
        migration_end_time=None,
    )

    mocked_project_metadata.get_or_new.return_value = mocked_project_metadata_instance

    identity_migrator = IdentityMigrator(project_id)

    # When
    status = identity_migrator.migration_status

    # Then
    assert status == ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS
    mocked_project_metadata.get_or_new.assert_called_with(project_id)
