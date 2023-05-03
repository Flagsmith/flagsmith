from audit.models import AuditLog
from audit.signals import send_environments_to_dynamodb


def test_send_env_to_dynamodb_from_audit_log_with_environment(
    dynamo_enabled_project_environment_one, mocker
):
    # Given
    mock_environment_model_class = mocker.patch("audit.signals.Environment")
    audit_log = AuditLog(environment=dynamo_enabled_project_environment_one)

    # When
    send_environments_to_dynamodb(sender=AuditLog, instance=audit_log)

    # Then
    mock_environment_model_class.write_environments_to_dynamodb.assert_called_once_with(
        environment_id=dynamo_enabled_project_environment_one.id, project_id=None
    )


def test_send_env_to_dynamodb_from_audit_log_with_project(
    dynamo_enabled_project, mocker
):
    # Given
    mock_environment_model_class = mocker.patch("audit.signals.Environment")
    audit_log = AuditLog(project=dynamo_enabled_project)

    # When
    send_environments_to_dynamodb(sender=AuditLog, instance=audit_log)

    # Then
    mock_environment_model_class.write_environments_to_dynamodb.assert_called_once_with(
        project_id=dynamo_enabled_project.id, environment_id=None
    )


def test_send_env_to_dynamodb_from_audit_log_with_environment_and_project(
    dynamo_enabled_project, dynamo_enabled_project_environment_one, mocker
):
    # Given
    mock_environment_model_class = mocker.patch("audit.signals.Environment")
    audit_log = AuditLog(
        environment=dynamo_enabled_project_environment_one,
        project=dynamo_enabled_project,
    )

    # When
    send_environments_to_dynamodb(sender=AuditLog, instance=audit_log)

    # Then
    mock_environment_model_class.write_environments_to_dynamodb.assert_called_once_with(
        environment_id=dynamo_enabled_project_environment_one.id,
        project_id=dynamo_enabled_project.id,
    )
