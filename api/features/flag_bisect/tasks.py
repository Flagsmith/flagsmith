from datetime import timedelta

from django.conf import settings
from task_processor.decorators import register_recurring_task

from features.flag_bisect import services


@register_recurring_task(run_every=timedelta(seconds=30))
def run_flag_bisect_swarm() -> None:
    """One swarm pass: Sentinel per environment with recent signals, then probes."""
    if settings.FLAG_BISECT_ENABLED:
        services.run_swarm()
