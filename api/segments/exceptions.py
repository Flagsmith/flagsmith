from rest_framework import status
from rest_framework.exceptions import APIException


class SystemSegmentModificationError(APIException):
    """A user tried to change a system segment, or one of its overrides."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "system_segment_modification"
    default_detail = "System segments and their overrides can't be changed directly."

    def __init__(self) -> None:
        # DRF's default exception handler renders `detail` alone.
        super().__init__({"detail": self.default_detail, "code": self.default_code})
