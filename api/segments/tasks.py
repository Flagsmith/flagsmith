from task_processor.decorators import register_task_handler

from segments.models import Segment


@register_task_handler()
def delete_segment(segment_id: int) -> None:
    Segment.objects.get(pk=segment_id).delete()
