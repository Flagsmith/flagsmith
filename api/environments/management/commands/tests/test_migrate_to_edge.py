import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


def test_calling_migrate_to_edge_calls_migrate_identities_with_correct_arguments(
    mocker,
):
    # Given
    project_id = 1
    mocked_dynamo_wrapper = mocker.patch(
        "environments.management.commands.migrate_to_edge.DynamoIdentityWrapper"
    )
    mocked_can_migrate = mocker.MagicMock(return_value=True)
    mocked_dynamo_wrapper.return_value.can_migrate = mocked_can_migrate

    # When
    call_command("migrate_to_edge", project_id)

    # Then
    mocked_dynamo_wrapper.assert_called_with()
    mocked_can_migrate.assert_called_with(project_id)
    mocked_dynamo_wrapper.return_value.migrate_identities.assert_called_with(project_id)


def test_calling_migrate_to_edge_raises_command_error_if_identities_are_already_migrated(
    mocker,
):
    # Given
    project_id = 1
    mocked_dynamo_wrapper = mocker.patch(
        "environments.management.commands.migrate_to_edge.DynamoIdentityWrapper"
    )
    mocked_can_migrate = mocker.MagicMock(return_value=False)
    mocked_dynamo_wrapper.return_value.can_migrate = mocked_can_migrate

    # When
    with pytest.raises(CommandError):
        call_command("migrate_to_edge", project_id)

    # Then
    mocked_dynamo_wrapper.assert_called_with()
    mocked_can_migrate.assert_called_with(project_id)
    mocked_dynamo_wrapper.return_value.migrate_identities.assert_not_called()
