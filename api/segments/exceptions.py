from rest_framework import status

from core.exceptions import APIError


class SystemSegmentModificationError(APIError):
    """A user tried to change a system segment, or one of its overrides."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "system_segment_modification"
    default_detail = "System segments and their overrides can't be changed directly."
