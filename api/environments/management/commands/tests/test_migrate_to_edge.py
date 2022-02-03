import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


def test_calling_migrate_to_edge_calls_migrate_identities_with_correct_arguments(
    mocker, project
):
    # Given
    mocked_dynamo_wrapper = mocker.patch(
        "environments.management.commands.migrate_to_edge.DynamoIdentityWrapper"
    )
    mocked_is_migration_done = mocker.MagicMock(return_value=False)
    mocked_dynamo_wrapper.return_value.is_migration_done = mocked_is_migration_done

    # When
    call_command("migrate_to_edge", project.id)

    # Then
    mocked_dynamo_wrapper.assert_called_with()
    mocked_is_migration_done.assert_called_with(project.id)
    mocked_dynamo_wrapper.return_value.migrate_identities.assert_called_with(project.id)


def test_calling_migrate_to_edge_raises_command_error_if_identities_are_already_migrated(
    mocker, project
):
    # Given
    mocked_dynamo_wrapper = mocker.patch(
        "environments.management.commands.migrate_to_edge.DynamoIdentityWrapper"
    )
    mocked_is_migration_done = mocker.MagicMock(return_value=True)
    mocked_dynamo_wrapper.return_value.is_migration_done = mocked_is_migration_done

    # When
    with pytest.raises(CommandError):
        call_command("migrate_to_edge", project.id)

    # Then
    mocked_dynamo_wrapper.assert_called_with()
    mocked_is_migration_done.assert_called_with(project.id)
    mocked_dynamo_wrapper.return_value.migrate_identities.assert_not_called()


def test_calling_migrate_to_edge_with_force_calls_migrate_identities_for_already_migrated_project(
    mocker, project
):
    # Given
    mocked_dynamo_wrapper = mocker.patch(
        "environments.management.commands.migrate_to_edge.DynamoIdentityWrapper"
    )
    mocked_is_migration_done = mocker.MagicMock(return_value=True)
    mocked_dynamo_wrapper.return_value.is_migration_done = mocked_is_migration_done

    # When
    call_command("migrate_to_edge", project.id, "--force")

    # Then
    mocked_dynamo_wrapper.assert_called_with()
    mocked_is_migration_done.assert_called_with(project.id)
    mocked_dynamo_wrapper.return_value.migrate_identities.assert_called_with(project.id)
