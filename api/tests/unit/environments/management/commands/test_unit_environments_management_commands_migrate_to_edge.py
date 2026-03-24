import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from environments.dynamodb.migrator import IdentityMigrator


def test_migrate_to_edge__can_migrate__calls_migrate_with_correct_arguments(  # type: ignore[no-untyped-def]
    mocker,
):
    # Given
    project_id = 1
    mocked_identity_migrator = mocker.patch(
        "environments.management.commands.migrate_to_edge.IdentityMigrator",
        spec=IdentityMigrator,
    )
    mocked_identity_migrator.return_value.can_migrate = True

    # When
    call_command("migrate_to_edge", project_id)

    # Then
    mocked_identity_migrator.assert_called_with(project_id)
    mocked_identity_migrator.return_value.migrate.assert_called_with()


def test_migrate_to_edge__already_migrated__raises_command_error(  # type: ignore[no-untyped-def]
    mocker,
):
    # Given
    project_id = 1
    mocked_identity_migrator = mocker.patch(
        "environments.management.commands.migrate_to_edge.IdentityMigrator",
        spec=IdentityMigrator,
    )
    mocked_identity_migrator.return_value.can_migrate = False

    # When
    with pytest.raises(CommandError):
        call_command("migrate_to_edge", project_id)

    # Then
    mocked_identity_migrator.assert_called_with(project_id)
    mocked_identity_migrator.return_value.migrate.assert_not_called()
