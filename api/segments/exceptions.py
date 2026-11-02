from typing import TYPE_CHECKING

from rest_framework import status

from core.exceptions import APIError

if TYPE_CHECKING:
    from segments.models import SegmentManagedBy


class SystemSegmentModificationError(APIError):
    """A user tried to change a system segment, or one of its overrides."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "system_segment_modification"
    default_detail = "System segments and their overrides can't be changed directly."

    def __init__(self, managed_by: "SegmentManagedBy") -> None:
        message = self.default_detail
        if managed_by:
            owner = managed_by.label.lower()
            message += f" Change this one through {owner} instead."
        super().__init__(message)
