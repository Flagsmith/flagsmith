from django.db.models import Q

from audit.models import AuditLog
from audit.signals import (
    send_environments_to_dynamodb,
    trigger_environment_update_messages,
)


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
        Q(id=dynamo_enabled_project_environment_one.id)
    )


def test_trigger_environment_update_messages_from_audit_log_with_environment(
    dynamo_enabled_project_environment_one, mocker
):
    # Given
    send_environment_update_message = mocker.patch(
        "audit.signals.send_environment_update_message"
    )
    audit_log = AuditLog(environment=dynamo_enabled_project_environment_one)

    # When
    trigger_environment_update_messages(sender=AuditLog, instance=audit_log)

    # Then
    send_environment_update_message.delay.assert_called_once_with(
        args=(dynamo_enabled_project_environment_one.api_key,)
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
        Q(project=dynamo_enabled_project)
    )


def test_trigger_environment_update_messages_from_audit_log_with_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    dynamo_enabled_project_environment_two,
    mocker,
):
    # Given
    send_environment_update_messages = mocker.patch(
        "audit.signals.send_environment_update_messages"
    )
    audit_log = AuditLog(project=dynamo_enabled_project)

    # When
    trigger_environment_update_messages(sender=AuditLog, instance=audit_log)

    # Then
    environment_api_keys = [
        dynamo_enabled_project_environment_one.api_key,
        dynamo_enabled_project_environment_two.api_key,
    ]
    send_environment_update_messages.delay.assert_called_once_with(
        args=(environment_api_keys,)
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
        Q(id=dynamo_enabled_project_environment_one.id)
    )


def test_trigger_environment_update_messages_from_audit_log_with_environment_and_project(
    dynamo_enabled_project, dynamo_enabled_project_environment_one, mocker
):
    # Given
    send_environment_update_message = mocker.patch(
        "audit.signals.send_environment_update_message"
    )
    audit_log = AuditLog(
        environment=dynamo_enabled_project_environment_one,
        project=dynamo_enabled_project,
    )

    # When
    trigger_environment_update_messages(sender=AuditLog, instance=audit_log)

    # Then
    send_environment_update_message.delay.assert_called_once_with(
        args=(dynamo_enabled_project_environment_one.api_key,)
    )
