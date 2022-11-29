from integrations.lead_tracking.pipedrive.lead_tracker import (
    PipedriveLeadTracker,
)
from task_processor.decorators import register_task_handler
from users.models import FFAdminUser

_pipedrive = None


@register_task_handler()
def create_pipedrive_lead(user_id: int):
    pipedrive = _get_pipedrive_lead_tracker()
    user = FFAdminUser.objects.get(id=user_id)
    pipedrive.create_lead(user)


def _get_pipedrive_lead_tracker():
    global _pipedrive
    if not _pipedrive:
        _pipedrive = PipedriveLeadTracker()
    return _pipedrive
