from task_processor.decorators import (  # type: ignore[import-untyped]
    register_task_handler,
)

from segments.models import Segment


@register_task_handler()  # type: ignore[misc]
def delete_segment(segment_id: int) -> None:
    Segment.objects.get(pk=segment_id).delete()
