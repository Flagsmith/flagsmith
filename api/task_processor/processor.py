import traceback

from django.db.models import Count, Q
from django.utils import timezone

from task_processor.models import Task, TaskResult, TaskRun


def run_next_task():
    next_task = (
        Task.objects.annotate(
            num_failures=Count(
                "task_runs", filter=Q(task_runs__result=TaskResult.FAILURE)
            )
        )
        .exclude(task_runs__result=TaskResult.SUCCESS)
        .filter(num_failures__lte=3)
        .order_by("scheduled_for")
        .first()
    )
    if not next_task:
        return

    task_run = TaskRun(started_at=timezone.now(), task=next_task)

    try:
        next_task.run()
        task_run.result = TaskResult.SUCCESS
        task_run.finished_at = timezone.now()
    except Exception:
        task_run.result = TaskResult.FAILURE
        task_run.error_details = str(traceback.format_exc)
    finally:
        task_run.save()
