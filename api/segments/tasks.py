from task_processor.decorators import (
    register_task_handler,
)

from audit.constants import SEGMENT_DELETED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from segments.models import Segment


@register_task_handler()
def delete_segment(segment_id: int) -> None:
    Segment.objects.get(pk=segment_id).delete()


@register_task_handler()
def create_segment_deleted_audit_log(
    project_id: int,
    segment_name: str,
    segment_id: int,
    segment_uuid: str,
    user_id: int | None,
    master_api_key_id: int | None,
    created_date: str,
) -> None:
    from django.utils.dateparse import parse_datetime

    AuditLog.objects.create(
        project_id=project_id,
        environment=None,
        log=SEGMENT_DELETED_MESSAGE % segment_name,
        author_id=user_id,
        master_api_key_id=master_api_key_id,
        related_object_id=segment_id,
        related_object_type=RelatedObjectType.SEGMENT.name,
        related_object_uuid=segment_uuid,
        created_date=parse_datetime(created_date),
    )
