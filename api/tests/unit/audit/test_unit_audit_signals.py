import json

from flag_engine.django_transform.document_builders import (
    build_environment_document,
)

from audit.models import AuditLog
from audit.signals import send_environments_to_dynamodb


def test_send_env_to_dynamodb_from_audit_log_with_environment(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_table,
):
    # Given
    audit_log = AuditLog.objects.create(
        environment=dynamo_enabled_project_environment_one
    )
    mock_dynamo_env_table.reset_mock()
    batch_writer = mock_dynamo_env_table.batch_writer.return_value
    batch_writer_context_manager = batch_writer.__enter__.return_value

    # When
    send_environments_to_dynamodb(sender=AuditLog, instance=audit_log)

    # Then
    batch_writer_context_manager.put_item.assert_called_once_with(
        Item=build_environment_document(dynamo_enabled_project_environment_one)
    )


def test_send_env_to_dynamodb_from_audit_log_with_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    dynamo_enabled_project_environment_two,
    mock_dynamo_env_table,
):
    # Given
    audit_log = AuditLog.objects.create(project=dynamo_enabled_project)
    mock_dynamo_env_table.reset_mock()
    batch_writer = mock_dynamo_env_table.batch_writer.return_value
    batch_writer_context_manager = batch_writer.__enter__.return_value

    # When
    send_environments_to_dynamodb(sender=AuditLog, instance=audit_log)

    # Then
    # put item is called twice
    assert batch_writer_context_manager.put_item.call_count == 2

    # and the two items are the 2 environment dicts as expected
    # note that we json dump the dicts so we can use sets as we don't
    # care about order and dicts are unhashable.
    put_item_items = {
        json.dumps(call_args[1]["Item"])
        for call_args in batch_writer_context_manager.put_item.call_args_list
    }
    expected_items = {
        json.dumps(build_environment_document(env))
        for env in (
            dynamo_enabled_project_environment_one,
            dynamo_enabled_project_environment_two,
        )
    }
    assert put_item_items == expected_items


def test_send_env_to_dynamodb_from_audit_log_with_environment_and_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_table,
):
    # Given
    audit_log = AuditLog.objects.create(
        environment=dynamo_enabled_project_environment_one,
        project=dynamo_enabled_project,
    )
    mock_dynamo_env_table.reset_mock()
    batch_writer = mock_dynamo_env_table.batch_writer.return_value
    batch_writer_context_manager = batch_writer.__enter__.return_value

    # When
    send_environments_to_dynamodb(sender=AuditLog, instance=audit_log)

    # Then
    batch_writer_context_manager.put_item.assert_called_once_with(
        Item=build_environment_document(dynamo_enabled_project_environment_one)
    )
