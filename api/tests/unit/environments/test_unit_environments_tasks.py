from datetime import timedelta

from django.utils import timezone
from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from task_processor.task_run_method import TaskRunMethod

from audit.models import AuditLog
from environments.models import Environment
from environments.tasks import (
    delete_environment_from_dynamo,
    process_environment_update,
    rebuild_environment_document,
)
from features.models import Feature


def test_rebuild_environment_document__valid_environment__calls_write_documents(
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


def test_process_environment_update__environment_audit_log__sends_environment_message(  # type: ignore[no-untyped-def]
    environment, mocker
):
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


def test_process_environment_update__project_audit_log__sends_project_message(  # type: ignore[no-untyped-def]
    environment, mocker
):
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


def test_process_environment_update__environment_is_creating__defers_write(
    environment: Environment,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR
    Environment.objects.filter(id=environment.id).update(is_creating=True)
    audit_log = AuditLog.objects.create(
        project=environment.project, environment=environment
    )
    mock_write_environment_documents = mocker.patch(
        "environments.tasks.Environment.write_environment_documents",
    )
    mock_task = mocker.patch("environments.tasks.process_environment_update")

    # When
    with freeze_time("2099-01-01T00:00:00Z"):
        process_environment_update(audit_log_id=audit_log.id)
        expected_delay_until = timezone.now() + timedelta(seconds=1)

    # Then
    mock_write_environment_documents.assert_not_called()
    mock_task.delay.assert_called_once_with(
        kwargs={"audit_log_id": audit_log.id, "deferrals": 1},
        delay_until=expected_delay_until,
    )


def test_process_environment_update__feature_is_creating__defers_write(
    environment: Environment,
    feature: Feature,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR
    Feature.objects.filter(id=feature.id).update(is_creating=True)
    audit_log = AuditLog.objects.create(
        project=environment.project, environment=environment
    )
    mock_write_environment_documents = mocker.patch(
        "environments.tasks.Environment.write_environment_documents",
    )
    mock_task = mocker.patch("environments.tasks.process_environment_update")

    # When
    process_environment_update(audit_log_id=audit_log.id)

    # Then
    mock_write_environment_documents.assert_not_called()
    mock_task.delay.assert_called_once()


def test_process_environment_update__deferrals_exhausted__writes_document_and_warns(
    environment: Environment,
    settings: SettingsWrapper,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR
    Environment.objects.filter(id=environment.id).update(is_creating=True)
    audit_log = AuditLog.objects.create(
        project=environment.project, environment=environment
    )
    mock_write_environment_documents = mocker.patch(
        "environments.tasks.Environment.write_environment_documents",
    )
    mock_task = mocker.patch("environments.tasks.process_environment_update")

    # When
    process_environment_update(audit_log_id=audit_log.id, deferrals=3)

    # Then
    mock_task.delay.assert_not_called()
    mock_write_environment_documents.assert_called_once_with(
        environment_id=environment.id, project_id=environment.project.id
    )
    assert log.has(
        "environment_document.written_while_seeding",
        level="warning",
        audit_log__id=audit_log.id,
        environment__id=environment.id,
        project__id=environment.project.id,
    )


def test_process_environment_update__no_task_processor__writes_document(
    environment: Environment,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    # `delay_until` is a no-op outside the task processor, so deferring would drop
    # the write instead of retrying it.
    settings.TASK_RUN_METHOD = TaskRunMethod.SEPARATE_THREAD
    mock_is_seeding = mocker.patch("environments.tasks._is_seeding_feature_states")
    Environment.objects.filter(id=environment.id).update(is_creating=True)
    audit_log = AuditLog.objects.create(
        project=environment.project, environment=environment
    )
    mock_write_environment_documents = mocker.patch(
        "environments.tasks.Environment.write_environment_documents",
    )
    mock_task = mocker.patch("environments.tasks.process_environment_update")

    # When
    process_environment_update(audit_log_id=audit_log.id)

    # Then
    mock_task.delay.assert_not_called()
    mock_write_environment_documents.assert_called_once_with(
        environment_id=environment.id, project_id=environment.project.id
    )
    # The `is_creating` check is skipped entirely, since it could not be acted on.
    mock_is_seeding.assert_not_called()


def test_delete_environment_from_dynamo__valid_environment__calls_all_wrappers(
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
