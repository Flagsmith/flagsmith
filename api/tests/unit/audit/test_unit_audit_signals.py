from pytest_django.asserts import assertQuerysetEqual as assert_queryset_equal

from audit.models import AuditLog
from audit.signals import send_environments_to_dynamodb
from environments.models import Environment


def test_send_env_to_dynamodb_from_audit_log_with_environment(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_wrapper,
):
    # Given
    audit_log = AuditLog.objects.create(
        environment=dynamo_enabled_project_environment_one
    )
    mock_dynamo_env_wrapper.reset_mock()

    # When
    send_environments_to_dynamodb(sender=AuditLog, instance=audit_log)

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0],
        Environment.objects.filter(id=dynamo_enabled_project_environment_one.id),
    )


def test_send_env_to_dynamodb_from_audit_log_with_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    dynamo_enabled_project_environment_two,
    mock_dynamo_env_wrapper,
):
    # Given
    audit_log = AuditLog.objects.create(project=dynamo_enabled_project)
    mock_dynamo_env_wrapper.reset_mock()

    # When
    send_environments_to_dynamodb(sender=AuditLog, instance=audit_log)

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0], Environment.objects.filter(project=dynamo_enabled_project)
    )


def test_send_env_to_dynamodb_from_audit_log_with_environment_and_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_wrapper,
):
    # Given
    audit_log = AuditLog.objects.create(
        environment=dynamo_enabled_project_environment_one,
        project=dynamo_enabled_project,
    )
    mock_dynamo_env_wrapper.reset_mock()

    # When
    send_environments_to_dynamodb(sender=AuditLog, instance=audit_log)

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0],
        Environment.objects.filter(id=dynamo_enabled_project_environment_one.id),
    )
