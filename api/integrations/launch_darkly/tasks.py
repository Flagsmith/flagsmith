import structlog
from task_processor.decorators import (
    register_task_handler,
)
from task_processor.exceptions import TaskBackoffError

from integrations.launch_darkly.exceptions import LaunchDarklyRateLimitError
from integrations.launch_darkly.models import LaunchDarklyImportRequest
from integrations.launch_darkly.services import process_import_request

logger = structlog.get_logger("launch_darkly")


@register_task_handler()
def process_launch_darkly_import_request(import_request_id: int) -> None:
    import_request = LaunchDarklyImportRequest.objects.get(id=import_request_id)
    log = logger.bind(
        import_request_id=import_request.id,
        ld_project_key=import_request.ld_project_key,
        organisation_id=import_request.project.organisation_id,
        project_id=import_request.project_id,
    )
    try:
        process_import_request(import_request)
    except LaunchDarklyRateLimitError as exc:
        log.warning(
            "import-rate-limit-reached",
            retry_at=exc.retry_at,
            error_message=str(exc),
        )
        raise TaskBackoffError(delay_until=exc.retry_at) from exc
