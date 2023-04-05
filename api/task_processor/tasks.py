import logging
from datetime import time, timedelta

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
    first_run_time=time(1, 0, 0),
)
def clean_up_old_tasks():
    now = timezone.now()
    delete_before = now - timedelta(days=settings.TASK_RETENTION_DAYS)

    # build the query
    query = Q(completed=True)
    if settings.TASK_DELETE_INCLUDE_FAILED_TASKS:
        query = query | Q(num_failures__gte=3)
    query = Q(scheduled_for__lt=delete_before) & query

    queryset = Task.objects.filter(query)
    while queryset.exists():
        # delete in batches of settings.TASK_DELETE_BATCH_SIZE
        Task.objects.filter(
            pk__in=queryset.values_list("id", flat=True)[
                0 : settings.TASK_DELETE_BATCH_SIZE  # noqa:E203
            ]
        ).delete()
