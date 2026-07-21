from django.utils import timezone
from task_processor.decorators import register_task_handler
from task_processor.models import TaskPriority

from app_analytics.types import KnownSDK
from environments.models import Environment


@register_task_handler(priority=TaskPriority.HIGH)
def record_environment_first_evaluation(
    api_key: str,
    sdk_label: KnownSDK,
) -> None:
    """Mark this environment as having been evaluated by a client SDK."""
    updated = Environment.objects.filter(
        api_key=api_key,
        first_evaluated_at__isnull=True,
    ).update(
        first_evaluated_at=timezone.now(),
        first_evaluated_sdk_label=sdk_label,
    )

    if updated:
        Environment.write_environment_documents(api_key=api_key)
