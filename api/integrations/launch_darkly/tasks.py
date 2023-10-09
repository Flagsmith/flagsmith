from django.db import transaction

from integrations.launch_darkly.models import LaunchDarklyImportRequest
from integrations.launch_darkly.services import process_import_request
from task_processor.decorators import register_task_handler


@register_task_handler()
def process_launch_darkly_import_request(import_request_id: int) -> None:
    with transaction.atomic():
        import_request = LaunchDarklyImportRequest.objects.get(id=import_request_id)
        process_import_request(import_request)
