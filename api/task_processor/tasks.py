import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)
from task_processor.models import HealthCheckModel, Task

logger = logging.getLogger(__name__)


@register_task_handler()
def create_health_check_model(health_check_model_uuid: str):
    logger.info("Creating health check model.")
    HealthCheckModel.objects.create(uuid=health_check_model_uuid)


@register_recurring_task(
    run_every=timedelta(days=1),
    kwargs={"task_retention_days": settings.TASK_RETENTION_DAYS},
)
def clean_up_old_tasks(task_retention_days: int):
    now = timezone.now()
    delete_before = now - timedelta(days=task_retention_days)

    query = Q(scheduled_for__lt=delete_before) & (
        Q(completed=True) | Q(num_failures__gte=3)
    )
    queryset = Task.objects.filter(query)
    while queryset.exists():
        # delete in batches of 2000
        queryset[0:2000].delete()
