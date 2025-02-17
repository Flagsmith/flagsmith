from pytest_django.asserts import assertQuerysetEqual as assert_queryset_equal

from environments.dynamodb.migrator import IdentityMigrator
from environments.dynamodb.types import (
    DynamoProjectMetadata,
    ProjectIdentityMigrationStatus,
)
from environments.identities.models import Identity
from environments.models import Environment, EnvironmentAPIKey


def test_migrate_calls_internal_methods_with_correct_arguments(  # type: ignore[no-untyped-def]
    mocker, project, identity, settings, environment_api_key
):
    # Given
    settings.EDGE_RELEASE_DATETIME = None

    assert project.enable_dynamo_db is False
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.migrator.DynamoProjectMetadata", autospec=True
    )
    mocked_environment_wrapper = mocker.patch(
        "environments.dynamodb.migrator.DynamoEnvironmentWrapper", autospec=True
    )
    mocked_api_key_wrapper = mocker.patch(
        "environments.dynamodb.migrator.DynamoEnvironmentAPIKeyWrapper", autospec=True
    )
    mocked_project_metadata_instance = mocker.MagicMock(
        spec=DynamoProjectMetadata, id=project.id
    )
    mocked_project_metadata.get_or_new.return_value = mocked_project_metadata_instance

    mocked_identity_wrapper = mocker.patch(
        "environments.dynamodb.migrator.DynamoIdentityWrapper", autospec=True
    )

    identity_migrator = IdentityMigrator(project.id)  # type: ignore[no-untyped-call]

    # When
    identity_migrator.migrate()  # type: ignore[no-untyped-call]

    # Then
    mocked_identity_wrapper.assert_called_with()

    args, kwargs = mocked_identity_wrapper.return_value.write_identities.call_args
    assert kwargs == {}

    assert_queryset_equal(
        args[0], Identity.objects.filter(environment__project__id=project.id)
    )
    # and
    args, kwargs = mocked_environment_wrapper.return_value.write_environments.call_args
    assert kwargs == {}

    assert_queryset_equal(args[0], Environment.objects.filter(project_id=project.id))

    # and
    args, kwargs = mocked_api_key_wrapper.return_value.write_api_keys.call_args
    assert kwargs == {}

    assert_queryset_equal(
        args[0], EnvironmentAPIKey.objects.filter(environment__project_id=project.id)
    )

    # and, Make sure that Project Metadata Wrapper was called correctly
    mocked_project_metadata.get_or_new.assert_called_with(project.id)
    mocked_project_metadata_instance.finish_identity_migration.assert_called_once_with()
    project.refresh_from_db()

    # and enable dynamodb was updated to True
    assert project.enable_dynamo_db is True


def test_trigger_migration_calls_internal_methods_with_correct_arguments(  # type: ignore[no-untyped-def]
    mocker, project
):
    # Given
    mocked_project_metadata = mocker.patch(
        "environments.dynamodb.migrator.DynamoProjectMetadata"
    )
    mocked_send_migration_event = mocker.patch(
        "environments.dynamodb.migrator.send_migration_event", autospec=True
    )

    mocked_project_metadata_instance = mocker.MagicMock(
        spec=DynamoProjectMetadata, id=project.id
    )
    mocked_project_metadata.get_or_new.return_value = mocked_project_metadata_instance

    identity_migrator = IdentityMigrator(project.id)  # type: ignore[no-untyped-call]

    # When
    identity_migrator.trigger_migration()  # type: ignore[no-untyped-call]

    # Then
    mocked_project_metadata.get_or_new.assert_called_with(project.id)
    mocked_project_metadata_instance.trigger_identity_migration.assert_called_once_with()
    mocked_send_migration_event.assert_called_once_with(project.id)


def test_is_migration_done_returns_true_if_migration_is_completed(  # type: ignore[no-untyped-def]
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

    identity_migrator = IdentityMigrator(project_id)  # type: ignore[no-untyped-call]

    # Then
    assert identity_migrator.is_migration_done is True
    mocked_project_metadata.get_or_new.assert_called_with(project_id)


def test_can_migrate_returns_true_if_migration_was_not_started(  # type: ignore[no-untyped-def]
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

    identity_migrator = IdentityMigrator(project_id)  # type: ignore[no-untyped-call]

    # Then
    assert identity_migrator.can_migrate is True

    mocked_project_metadata.get_or_new.assert_called_with(project_id)


def test_get_migration_status_returns_correct_migraion_status_for_in_progress_migration(  # type: ignore[no-untyped-def]  # noqa: E501
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

    identity_migrator = IdentityMigrator(project_id)  # type: ignore[no-untyped-call]

    # When
    status = identity_migrator.migration_status

    # Then
    assert status == ProjectIdentityMigrationStatus.MIGRATION_IN_PROGRESS
    mocked_project_metadata.get_or_new.assert_called_with(project_id)
