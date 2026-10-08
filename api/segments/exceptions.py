from rest_framework import status
from rest_framework.exceptions import APIException

from segments.models import Segment, SegmentManagedBy


class SystemSegmentModificationError(APIException):
    """A user tried to change a system segment, or one of its overrides.

    System segments and their overrides are owned by the feature that created
    them, e.g. flag dependencies, experiments or release pipelines, and can
    only be changed through it.
    """

    status_code = status.HTTP_409_CONFLICT
    default_code = "system_segment_modification"

    def __init__(self, segment: Segment) -> None:
        managed_by = SegmentManagedBy(segment.managed_by)
        owner = (
            f"its {managed_by.label.lower()}"
            if managed_by != SegmentManagedBy.UNMANAGED
            else "the feature that created it"
        )
        super().__init__(
            f"System segment '{segment.name}' and its overrides cannot be "
            f"changed directly. Manage them through {owner} instead."
        )
