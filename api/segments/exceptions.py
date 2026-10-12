from rest_framework import status

from core.exceptions import APIError


class SystemSegmentModificationError(APIError):
    """A user tried to change a system segment, or one of its overrides."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "system_segment_modification"
    default_detail = "System segments and their overrides can't be changed directly."

    def __init__(self, managed_by: str = "") -> None:
        # Names the feature managing the segment, if any, e.g. "dependency".
        super().__init__(**({"managed_by": managed_by} if managed_by else {}))
