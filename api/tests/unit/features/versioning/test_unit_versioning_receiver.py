from datetime import timedelta
from unittest import mock

from django.utils import timezone

from features.versioning.receivers import update_environment_document


def test_update_environment_document__immediate_publish__does_not_schedule_rebuild() -> None:
    # Given
    mock_instance = mock.MagicMock()
    mock_instance.live_from = timezone.now() - timedelta(seconds=1)
    mock_instance.environment_id = 1

    # When
    with mock.patch(
        "features.versioning.receivers.rebuild_environment_document"
    ) as mock_rebuild:
        update_environment_document(instance=mock_instance)

    # Then
    mock_rebuild.delay.assert_not_called()


def test_update_environment_document__scheduled_publish__schedules_rebuild_at_live_from() -> None:
    # Given
    future = timezone.now() + timedelta(hours=1)
    mock_instance = mock.MagicMock()
    mock_instance.live_from = future
    mock_instance.environment_id = 1

    # When
    with mock.patch(
        "features.versioning.receivers.rebuild_environment_document"
    ) as mock_rebuild:
        update_environment_document(instance=mock_instance)

    # Then
    mock_rebuild.delay.assert_called_once_with(
        kwargs={"environment_id": 1},
        delay_until=future,
    )
