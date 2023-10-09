from audit.models import AuditLog
from environments.tasks import (
    process_environment_update,
    rebuild_environment_document,
)


def test_rebuild_environment_document(environment, mocker):
    # Given
    mock_dynamo_wrapper = mocker.MagicMock(is_enabled=True)
    mocker.patch(
        "environments.tasks.DynamoEnvironmentWrapper", return_value=mock_dynamo_wrapper
    )

    # When
    rebuild_environment_document(environment_id=environment.id)

    # Then
    mock_dynamo_wrapper.write_environment.assert_called_once_with(environment)


def test_process_environment_update_with_environment_audit_log(environment, mocker):
    # Given
    audit_log = AuditLog.objects.create(
        project=environment.project, environment=environment
    )
    mock_environment_model_class = mocker.patch(
        "environments.tasks.Environment", autospec=True
    )
    mock_send_environment_update_message_for_environment = mocker.patch(
        "environments.tasks.send_environment_update_message_for_environment",
        autospec=True,
    )
    mock_send_environment_update_message_for_project = mocker.patch(
        "environments.tasks.send_environment_update_message_for_project",
        autospec=True,
    )

    # When
    process_environment_update(audit_log_id=audit_log.id)

    # Then
    mock_environment_model_class.write_environments_to_dynamodb.assert_called_once_with(
        environment_id=environment.id, project_id=environment.project.id
    )
    mock_send_environment_update_message_for_environment.assert_called_once_with(
        environment
    )
    mock_send_environment_update_message_for_project.assert_not_called()


def test_process_environment_update_with_project_audit_log(environment, mocker):
    # Given
    audit_log = AuditLog.objects.create(project=environment.project)
    mock_environment_model_class = mocker.patch(
        "environments.tasks.Environment", autospec=True
    )
    mock_send_environment_update_message_for_environment = mocker.patch(
        "environments.tasks.send_environment_update_message_for_environment",
        autospec=True,
    )
    mock_send_environment_update_message_for_project = mocker.patch(
        "environments.tasks.send_environment_update_message_for_project",
        autospec=True,
    )

    # When
    process_environment_update(audit_log_id=audit_log.id)

    # Then
    mock_environment_model_class.write_environments_to_dynamodb.assert_called_once_with(
        environment_id=None, project_id=environment.project.id
    )
    mock_send_environment_update_message_for_environment.assert_not_called()
    mock_send_environment_update_message_for_project.assert_called_once_with(
        environment.project
    )
