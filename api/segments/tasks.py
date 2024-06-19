from segments.models import Segment
from task_processor.decorators import register_task_handler


@register_task_handler()
def delete_segment(segment_id: int) -> None:
    Segment.objects.get(pk=segment_id).delete()
