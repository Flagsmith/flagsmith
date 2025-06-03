from datetime import datetime

import pytest
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from task_processor.exceptions import TaskBackoffError

from integrations.launch_darkly.exceptions import LaunchDarklyRateLimitError
from integrations.launch_darkly.models import LaunchDarklyImportRequest
from integrations.launch_darkly.tasks import process_launch_darkly_import_request


def test_process_import_request__rate_limit__raises_expected(
    import_request: LaunchDarklyImportRequest,
    mocker: MockerFixture,
) -> None:
    # Given
    expected_delay_until = datetime.now()

    mocker.patch(
        "integrations.launch_darkly.tasks.process_import_request",
        side_effect=LaunchDarklyRateLimitError(retry_at=expected_delay_until),
    )

    # When & Then
    with pytest.raises(TaskBackoffError) as exc_info:
        process_launch_darkly_import_request(import_request_id=import_request.id)

    assert exc_info.value.delay_until == expected_delay_until


def test_process_import_request__hard_error__expected_task_status(
    import_request: LaunchDarklyImportRequest,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    mocker.patch(
        "integrations.launch_darkly.tasks.process_import_request",
        side_effect=Exception("Unexpected error"),
    )

    # When
    result = process_launch_darkly_import_request(import_request_id=import_request.id)

    # Then
    # The task didn't raise the exception...
    assert result is None
    # ...but logged it
    assert log.events == [
        {
            "event": "import-failed",
            "exc_info": True,
            "import_request_id": import_request.id,
            "ld_project_key": "test-project-key",
            "level": "error",
            "organisation_id": import_request.project.organisation_id,
            "project_id": import_request.project_id,
        },
    ]
