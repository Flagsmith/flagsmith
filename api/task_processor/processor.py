import logging
import traceback
import typing

from django.db import transaction
from django.utils import timezone

from task_processor.models import Task, TaskResult, TaskRun

logger = logging.getLogger(__name__)


@transaction.atomic
def run_tasks(num_tasks: int = 1) -> typing.Optional[typing.List[TaskRun]]:
    if num_tasks < 1:
        raise ValueError("Number of tasks to process must be at least one")

    tasks = (
        Task.objects.select_for_update(skip_locked=True)
        .filter(num_failures__lt=3, scheduled_for__lte=timezone.now(), completed=False)
        .order_by("scheduled_for")[:num_tasks]
    )
    if not tasks:
        logger.debug("No tasks to process.")
        return

    executed_tasks = []
    task_runs = []

    for task in tasks:
        executed_task, task_run = _run_task(task)
        executed_tasks.append(executed_task)
        task_runs.append(task_run)

    if executed_tasks:
        Task.objects.bulk_update(executed_tasks, fields=["completed", "num_failures"])

    if task_runs:
        TaskRun.objects.bulk_create(task_runs)

    return task_runs


def _run_task(task: Task) -> typing.Optional[typing.Tuple[Task, TaskRun]]:
    if task.task_runs.filter(result=TaskResult.SUCCESS).exists():
        # This should never happen due to the use of select_for_update above, but it's
        # best to guard against it rather than try and execute the task twice.
        logger.warning(
            "Task has already been processed successfully, not processing again."
        )
        return

    task_run = TaskRun(started_at=timezone.now(), task=task)

    try:
        task.run()
        task_run.result = TaskResult.SUCCESS

        task_run.finished_at = timezone.now()
        task.completed = True
    except Exception:
        task.num_failures += 1

        task_run.result = TaskResult.FAILURE
        task_run.error_details = str(traceback.format_exc())

    return task, task_run
