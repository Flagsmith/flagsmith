from projects.serializers import ProjectSerializer


def test_ProjectSerializer_get_is_identity_migration_done_calls_dynamo_wrapper_with_correct_arguments(
    mocker, project
):
    # Given
    is_migration_done = True
    mock_dynamo_wrapper = mocker.MagicMock()
    mock_dynamo_wrapper.is_migration_done.return_value = is_migration_done
    mocker.patch(
        "projects.serializers.DynamoIdentityWrapper", return_value=mock_dynamo_wrapper
    )

    # When
    serializer = ProjectSerializer()

    # Then
    serializer.get_is_identity_migration_done(project) is is_migration_done
    mock_dynamo_wrapper.is_migration_done.assert_called_with(project.id)


def test_ProjectSerializer_get_is_identity_migration_done_returns_false_if_dynamo_not_enabled(
    mocker, project
):
    # Given
    mocked_dynamo_wrapper = mocker.patch("projects.serializers.DynamoIdentityWrapper")
    mocked_dynamo_wrapper.return_value.is_enabled = False

    # When
    serializer = ProjectSerializer()

    # Then
    serializer.get_is_identity_migration_done(project) is False

    # and
    mocked_dynamo_wrapper.assert_called_with()
    mocked_dynamo_wrapper.return_value.is_migration_done.assert_not_called()
