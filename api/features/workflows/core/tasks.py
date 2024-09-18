from task_processor.decorators import register_task_handler

from features.workflows.core.models import ChangeRequest


@register_task_handler()
def delete_change_request(change_request_id: int) -> None:
    ChangeRequest.objects.get(pk=change_request_id).delete()
