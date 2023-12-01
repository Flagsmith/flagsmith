from datetime import timedelta

from django.utils import timezone

from task_processor.models import Task
from task_processor.statistics import get_task_queue_statistics


def test_get_task_queue_statistics(db: None) -> None:
    # Given
    now = timezone.now()
    stuck_task_threshold_seconds = 180

    Task.objects.create(
        task_identifier="tasks.waiting_task",
        scheduled_for=now - timedelta(milliseconds=10),
        is_locked=False,
    )
    Task.objects.create(
        task_identifier="tasks.stuck",
        scheduled_for=now - timedelta(seconds=stuck_task_threshold_seconds + 1),
        is_locked=True,
    )
    Task.objects.create(
        task_identifier="tasks.in_flight",
        scheduled_for=now - timedelta(milliseconds=10),
        is_locked=True,
    )
    Task.objects.create(
        task_identifier="tasks.scheduled_task", scheduled_for=now + timedelta(seconds=1)
    )
    Task.objects.create(
        task_identifier="tasks.completed_task",
        scheduled_for=now - timedelta(seconds=1),
        completed=True,
    )
    Task.objects.create(
        task_identifier="tasks.failed_task",
        scheduled_for=now - timedelta(seconds=1),
        completed=False,
        num_failures=3,
    )

    # When
    stats = get_task_queue_statistics()

    # Then
    assert stats.waiting == 1
    assert stats.stuck == 1
    assert stats.in_flight == 1
