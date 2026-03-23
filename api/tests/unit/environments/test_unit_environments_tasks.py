import pytest
from django.db import OperationalError
from pytest_mock import MockerFixture
from task_processor.exceptions import TaskBackoffError

from audit.models import AuditLog
from environments.models import Environment
from environments.tasks import (
    delete_environment,
    delete_environment_from_dynamo,
    process_environment_update,
    rebuild_environment_document,
)


def test_rebuild_environment_document(
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_write_environment_documents = mocker.patch(
        "environments.tasks.Environment.write_environment_documents",
    )

    # When
    rebuild_environment_document(environment_id=environment.id)

    # Then
    mock_write_environment_documents.assert_called_once_with(
        environment_id=environment.id
    )


def test_process_environment_update_with_environment_audit_log(environment, mocker):  # type: ignore[no-untyped-def]
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
    mock_environment_model_class.write_environment_documents.assert_called_once_with(
        environment_id=environment.id, project_id=environment.project.id
    )
    mock_send_environment_update_message_for_environment.assert_called_once_with(
        environment
    )
    mock_send_environment_update_message_for_project.assert_not_called()


def test_process_environment_update_with_project_audit_log(environment, mocker):  # type: ignore[no-untyped-def]
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
    mock_environment_model_class.write_environment_documents.assert_called_once_with(
        environment_id=None, project_id=environment.project.id
    )
    mock_send_environment_update_message_for_environment.assert_not_called()
    mock_send_environment_update_message_for_project.assert_called_once_with(
        environment.project
    )


def test_delete_environment__calls_internal_methods_correctly(
    mocker: MockerFixture,
) -> None:
    # Given
    environment_api_key = "test-api-key"
    environment_id = 10

    mocked_environment_wrapper = mocker.patch("environments.tasks.environment_wrapper")
    mocked_environment_v2_wrapper = mocker.patch(
        "environments.tasks.environment_v2_wrapper"
    )
    DynamoIdentityWrapper = mocker.patch("environments.tasks.DynamoIdentityWrapper")
    mocked_identity_wrapper = DynamoIdentityWrapper.return_value

    # When
    delete_environment_from_dynamo(environment_api_key, environment_id)  # type: ignore[arg-type]

    # Then
    mocked_environment_wrapper.delete_environment.assert_called_once_with(
        environment_api_key
    )

    mocked_environment_v2_wrapper.delete_environment.assert_called_once_with(
        environment_id
    )
    mocked_identity_wrapper.delete_all_identities.assert_called_once_with(
        environment_api_key
    )


def test_delete_environment__environment_does_not_exist__succeeds_silently(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_get_environment = mocker.patch("environments.tasks.Environment.objects.get")
    mock_get_environment.side_effect = Environment.DoesNotExist

    # When
    delete_environment(environment_id=1)

    # Then
    # No exception is raised, confirming silent success
    mock_get_environment.assert_called_once_with(id=1)


def test_delete_environment__database_deadlock__raises_task_backoff_error(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_get_environment = mocker.patch("environments.tasks.Environment.objects.get")
    mock_get_environment.side_effect = OperationalError

    # When
    with pytest.raises(TaskBackoffError):
        delete_environment(environment_id=1)

    # Then
    # TaskBackoffError is raised to trigger the task-processor retry
    mock_get_environment.assert_called_once_with(id=1)  # Given
    mock_get_environment = mocker.patch("environments.tasks.Environment.objects.get")
    mock_get_environment.side_effect = OperationalError

    # When
    with pytest.raises(TaskBackoffError):
        delete_environment(environment_id=1)

    # Then
    # TaskBackoffError is raised to trigger the task-processor retry
    mock_get_environment.assert_called_once_with(id=1)
