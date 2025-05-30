from datetime import datetime

import pytest
from pytest_mock import MockerFixture
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
