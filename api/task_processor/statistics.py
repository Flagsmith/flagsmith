from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from task_processor.models import Task


@dataclass
class TaskQueueStatistics:
    waiting: int
    stuck: int
    in_flight: int


def get_task_queue_statistics(
    stuck_task_threshold_seconds: int = 180,
) -> TaskQueueStatistics:
    now = timezone.now()
    stuck_task_threshold = now - timedelta(seconds=stuck_task_threshold_seconds)

    _base_unprocessed_task_query = Q(
        num_failures__lt=3, completed=False, scheduled_for__lte=now
    )
    waiting_tasks_query = _base_unprocessed_task_query & Q(is_locked=False)
    in_flight_tasks_query = _base_unprocessed_task_query & Q(
        scheduled_for__gte=stuck_task_threshold, is_locked=True
    )
    stuck_tasks_query = _base_unprocessed_task_query & Q(
        scheduled_for__lte=stuck_task_threshold, is_locked=True
    )

    return TaskQueueStatistics(
        waiting=Task.objects.filter(waiting_tasks_query).count(),
        in_flight=Task.objects.filter(in_flight_tasks_query).count(),
        stuck=Task.objects.filter(stuck_tasks_query).count(),
    )
