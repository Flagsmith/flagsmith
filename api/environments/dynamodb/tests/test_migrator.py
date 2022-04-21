from pytest_django.asserts import assertQuerysetEqual

from environments.dynamodb.migrator import IdentityMigrator
from environments.dynamodb.types import (
    DynamoProjectMetadata,
    ProjectIdentityMigrationStatus,
)
from environments.identities.models import Identity
from environments.models import Environment


def test_migrate_calls_internal_methods_with_correct_arguments(
    mocker, project, identity
):
    # Given
    assert project.enable_dynamo_db is False
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.migrator.DynamoProjectMetadata"
    )
    mocked_environment_wrapper = mocked_identity_wrapper = mocker.patch(
        "environments.dynamodb.migrator.DynamoEnvironmentWrapper"
    )
    mocked_project_metadata_instance = mocker.MagicMock(
        spec=DynamoProjectMetadata, id=project.id
    )
    mocked_project_metadata.get_or_new.return_value = mocked_project_metadata_instance

    mocked_identity_wrapper = mocker.patch(
        "environments.dynamodb.migrator.DynamoIdentityWrapper"
    )

    identity_migrator = IdentityMigrator(project.id)

    # When
    identity_migrator.migrate()

    # Then
    mocked_identity_wrapper.assert_called_with()

    args, kwargs = mocked_identity_wrapper.return_value.write_identities.call_args
    assert kwargs == {}

    assertQuerysetEqual(
        args[0], Identity.objects.filter(environment__project__id=project.id)
    )
    # and
    args, kwargs = mocked_environment_wrapper.return_value.write_environments.call_args
    assert kwargs == {}

    assertQuerysetEqual(args[0], Environment.objects.filter(project_id=project.id))

    # and, Make sure that Project Metadata Wrapper was called correctly
    mocked_project_metadata.get_or_new.assert_called_with(project.id)
    mocked_project_metadata_instance.start_identity_migration.assert_called_once_with()
    mocked_project_metadata_instance.finish_identity_migration.assert_called_once_with()
    project.refresh_from_db()

    # and enable dynamodb was updated to True
    assert project.enable_dynamo_db is True


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
        identity_migration_status=ProjectIdentityMigrationStatus.MIGRATION_COMPLETED,
    )

    mocked_project_metadata.get_or_new.return_value = mocked_project_metadata_instance

    identity_migrator = IdentityMigrator(project_id)

    # Then
    assert identity_migrator.is_migration_done is True
    mocked_project_metadata.get_or_new.assert_called_with(project_id)


def test_can_migrate_returns_true_if_migration_was_not_started(
    mocker,
):
    # Given
    project_id = 1
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.migrator.DynamoProjectMetadata"
    )
    mocked_project_metadata_instance = mocker.MagicMock(
        spec=DynamoProjectMetadata,
        identity_migration_status=ProjectIdentityMigrationStatus.MIGRATION_NOT_STARTED,
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
        identity_migration_status=ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS,
    )

    mocked_project_metadata.get_or_new.return_value = mocked_project_metadata_instance

    identity_migrator = IdentityMigrator(project_id)

    # When
    status = identity_migrator.migration_status

    # Then
    assert status == ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS
    mocked_project_metadata.get_or_new.assert_called_with(project_id)
