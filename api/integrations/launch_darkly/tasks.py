from task_processor.decorators import register_task_handler  # type: ignore[import-untyped]

from integrations.launch_darkly.models import LaunchDarklyImportRequest
from integrations.launch_darkly.services import process_import_request


@register_task_handler()  # type: ignore[misc]
def process_launch_darkly_import_request(import_request_id: int) -> None:
    import_request = LaunchDarklyImportRequest.objects.get(id=import_request_id)
    process_import_request(import_request)
