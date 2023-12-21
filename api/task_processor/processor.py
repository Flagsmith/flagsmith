import logging
import traceback
import typing
from datetime import timedelta

from django.utils import timezone

from task_processor.models import (
    RecurringTask,
    RecurringTaskRun,
    Task,
    TaskResult,
    TaskRun,
)

logger = logging.getLogger(__name__)

UNREGISTERED_RECURRING_TASK_GRACE_PERIOD = timedelta(minutes=30)


def run_tasks(num_tasks: int = 1) -> typing.List[TaskRun]:
    if num_tasks < 1:
        raise ValueError("Number of tasks to process must be at least one")

    tasks = Task.objects.get_tasks_to_process(num_tasks)

    if tasks:
        executed_tasks = []
        task_runs = []

        for task in tasks:
            task, task_run = _run_task(task)

            executed_tasks.append(task)
            task_runs.append(task_run)

        if executed_tasks:
            Task.objects.bulk_update(
                executed_tasks, fields=["completed", "num_failures", "is_locked"]
            )

        if task_runs:
            TaskRun.objects.bulk_create(task_runs)

        return task_runs

    logger.debug("No tasks to process.")
    return []


def run_recurring_tasks(num_tasks: int = 1) -> typing.List[RecurringTaskRun]:
    if num_tasks < 1:
        raise ValueError("Number of tasks to process must be at least one")

    # NOTE: We will probably see a lot of delay in the execution of recurring tasks
    # if the tasks take longer then `run_every` to execute. This is not
    # a problem for now, but we should be mindful of this limitation
    tasks = RecurringTask.objects.get_tasks_to_process(num_tasks)
    if tasks:
        task_runs = []

        for task in tasks:
            if not task.is_task_registered:
                # This is necessary to ensure that old instances of the task processor,
                # which may still be running during deployment, do not remove tasks added by new instances.
                # Reference: https://github.com/Flagsmith/flagsmith/issues/2551
                if (
                    timezone.now() - task.created_at
                ) > UNREGISTERED_RECURRING_TASK_GRACE_PERIOD:
                    task.delete()
                continue

            if task.should_execute:
                task, task_run = _run_task(task)
                task_runs.append(task_run)
            else:
                task.unlock()

        # update all tasks that were not deleted
        to_update = [task for task in tasks if task.id]
        RecurringTask.objects.bulk_update(to_update, fields=["is_locked"])

        if task_runs:
            RecurringTaskRun.objects.bulk_create(task_runs)

        return task_runs

    logger.debug("No tasks to process.")
    return []


def _run_task(task: typing.Union[Task, RecurringTask]) -> typing.Tuple[Task, TaskRun]:
    task_run = task.task_runs.model(started_at=timezone.now(), task=task)

    try:
        task.run()
        task_run.result = TaskResult.SUCCESS

        task_run.finished_at = timezone.now()
        task.mark_success()
    except Exception as e:
        logger.warning(e)
        task.mark_failure()

        task_run.result = TaskResult.FAILURE
        task_run.error_details = str(traceback.format_exc())

    return task, task_run
