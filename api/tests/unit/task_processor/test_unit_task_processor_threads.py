import logging

from django.db import DatabaseError
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from task_processor.threads import TaskRunner
from tests.unit.task_processor.conftest import GetCaptureTaskProcessorLogger


def test_task_runner_is_resilient_to_database_errors(
    db: None,
    mocker: MockerFixture,
    capture_task_processor_logger: GetCaptureTaskProcessorLogger,
    settings: SettingsWrapper,
) -> None:
    # Given
    caplog = capture_task_processor_logger(logging.DEBUG)

    task_runner = TaskRunner()
    mocker.patch(
        "task_processor.threads.run_tasks", side_effect=DatabaseError("Database error")
    )

    # When
    task_runner.run_iteration()

    # Then
    assert len(caplog.records) == 2

    assert caplog.records[0].levelno == logging.ERROR
    assert (
        caplog.records[0].message
        == "Received database error retrieving tasks: Database error."
    )

    assert caplog.records[1].levelno == logging.DEBUG
    assert caplog.records[1].message.startswith("Traceback")
