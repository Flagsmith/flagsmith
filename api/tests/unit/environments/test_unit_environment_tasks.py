from environments.tasks import rebuild_environment_document


def test_rebuild_environment_document(environment, mocker):
    # Given
    mock_dynamo_wrapper = mocker.MagicMock()
    mocker.patch(
        "environments.tasks.DynamoEnvironmentWrapper", return_value=mock_dynamo_wrapper
    )

    # When
    rebuild_environment_document(environment_id=environment.id)

    # Then
    mock_dynamo_wrapper.write_environment.assert_called_once_with(environment)
