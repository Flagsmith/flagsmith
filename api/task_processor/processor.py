import traceback
import typing

from django.db import transaction
from django.utils import timezone

from task_processor.models import Task, TaskResult, TaskRun


def run_next_task() -> typing.Optional[TaskRun]:
    with transaction.atomic():
        available_tasks = (
            Task.objects.exclude(task_runs__result=TaskResult.SUCCESS)
            .filter(num_failures__lte=3, scheduled_for__lte=timezone.now())
            .select_for_update(skip_locked=True)
            .order_by("scheduled_for")
        )
        task = available_tasks.first()
        if not task:
            return

        task_run = TaskRun(started_at=timezone.now(), task=task)

        try:
            task.run()
            task_run.result = TaskResult.SUCCESS
            task_run.finished_at = timezone.now()
        except Exception:
            task.fail()
            task.save()

            task_run.result = TaskResult.FAILURE
            task_run.error_details = str(traceback.format_exc())
        finally:
            task_run.save()

        return task_run
