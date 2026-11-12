from datetime import timedelta

from task_processor.decorators import register_recurring_task

from telemetry.services import push_usage_snapshots


@register_recurring_task(run_every=timedelta(hours=24))
def push_usage() -> None:
    push_usage_snapshots()
