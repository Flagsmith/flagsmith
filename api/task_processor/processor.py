import logging
import traceback
import typing

from django.db import transaction
from django.utils import timezone

from task_processor.models import (
    RecurringTask,
    RecurringTaskRun,
    Task,
    TaskResult,
    TaskRun,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def run_tasks(num_tasks: int = 1) -> typing.List[TaskRun]:
    if num_tasks < 1:
        raise ValueError("Number of tasks to process must be at least one")

    tasks = (
        Task.objects.select_for_update(skip_locked=True)
        .filter(num_failures__lt=3, scheduled_for__lte=timezone.now(), completed=False)
        .order_by("scheduled_for")[:num_tasks]
    )
    if tasks:
        executed_tasks = []
        task_runs = []

        for task in tasks:
            executed_task, task_run = _run_task(task)
            executed_tasks.append(executed_task)
            task_runs.append(task_run)

        if executed_tasks:
            Task.objects.bulk_update(
                executed_tasks, fields=["completed", "num_failures"]
            )

        if task_runs:
            TaskRun.objects.bulk_create(task_runs)

        return task_runs

    logger.debug("No tasks to process.")
    return []


@transaction.atomic
def run_recurring_tasks(num_tasks: int = 1) -> typing.List[RecurringTask]:
    if num_tasks < 1:
        raise ValueError("Number of tasks to process must be at least one")

    tasks = RecurringTask.objects.select_for_update(skip_locked=True)[:num_tasks]
    if tasks:
        task_runs = []

        for task in tasks:
            # Remove the task if it's not registered anymore
            if not task.is_task_registered:
                task.delete()
                continue

            if task.should_execute:
                _, task_run = _run_task(task)
                task_runs.append(task_run)

        if task_runs:
            RecurringTaskRun.objects.bulk_create(task_runs)

        return task_runs

    logger.debug("No tasks to process.")
    return []


def _run_task(task: Task) -> typing.Optional[typing.Tuple[Task, TaskRun]]:
    task_run = task.task_runs.model(started_at=timezone.now(), task=task)

    try:
        task.run()
        task_run.result = TaskResult.SUCCESS

        task_run.finished_at = timezone.now()
        task.mark_success()
    except Exception:
        task.mark_failure()

        task_run.result = TaskResult.FAILURE
        task_run.error_details = str(traceback.format_exc())

    return task, task_run
