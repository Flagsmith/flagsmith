import logging
import traceback
import typing

from django.db import transaction
from django.utils import timezone

from task_processor.models import Task, TaskResult, TaskRun

logger = logging.getLogger(__name__)


@transaction.atomic
def run_next_task() -> typing.Optional[TaskRun]:
    task = (
        Task.objects.select_for_update(skip_locked=True)
        .filter(num_failures__lt=3, scheduled_for__lte=timezone.now(), completed=False)
        .order_by("scheduled_for")
        .first()
    )
    if not task:
        logger.debug("No tasks to process.")
        return

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
    finally:
        task_run.save()
        task.save()

    return task_run
