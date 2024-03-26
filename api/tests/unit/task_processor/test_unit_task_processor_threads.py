from _pytest.logging import LogCaptureFixture
from django.db import DatabaseError
from pytest_mock import MockerFixture

from task_processor.threads import TaskRunner


def test_task_runner_is_resilient_to_database_errors(
    db: None, mocker: MockerFixture, caplog: LogCaptureFixture
) -> None:
    # Given
    task_runner = TaskRunner()
    mocker.patch("task_processor.threads.run_tasks", side_effect=DatabaseError)

    # When
    task_runner.run_iteration()

    # Then
    # TODO: work out caplog issues...
    assert True  # exception is not raised
