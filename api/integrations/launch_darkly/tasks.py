from task_processor.decorators import (
    register_task_handler,
)
from task_processor.exceptions import TaskBackoffError

from integrations.launch_darkly.exceptions import LaunchDarklyRateLimitError
from integrations.launch_darkly.models import LaunchDarklyImportRequest
from integrations.launch_darkly.services import process_import_request


@register_task_handler()
def process_launch_darkly_import_request(import_request_id: int) -> None:
    import_request = LaunchDarklyImportRequest.objects.get(id=import_request_id)
    try:
        process_import_request(import_request)
    except LaunchDarklyRateLimitError as exc:
        raise TaskBackoffError(delay_until=exc.retry_at) from exc
