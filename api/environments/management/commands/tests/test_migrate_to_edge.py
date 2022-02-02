from django.core.management import call_command


def test_calling_migrate_to_edge_calls_migrate_identities_with_correct_arguments(
    mocker, project
):
    # Given
    mocked_dynamo_wrapper = mocker.patch(
        "environments.management.commands.migrate_to_edge.DynamoIdentityWrapper"
    )
    # When
    call_command("migrate_to_edge", project.id)

    # Then
    mocked_dynamo_wrapper.assert_called_with()
    mocked_dynamo_wrapper.return_value.migrate_identities.assert_called_with(project.id)
