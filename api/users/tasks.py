from integrations.lead_tracking.pipedrive.lead_tracker import (
    PipedriveLeadTracker,
)
from task_processor.decorators import register_task_handler
from users.models import FFAdminUser


@register_task_handler()
def create_pipedrive_lead(user_id: int):
    pipedrive = PipedriveLeadTracker()
    user = FFAdminUser.objects.get(id=user_id)
    pipedrive.create_lead(user)
