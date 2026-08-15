"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from rest_framework import status
from rest_framework.exceptions import APIException, NotFound


class ChangeRequestsEnabledError(APIException):
    """Raised where a flag can only be changed by going through a change request."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "change_requests_enabled"
    default_detail = (
        "Cannot update flags in an environment with change requests enabled."
    )

    def __init__(self) -> None:
        # DRF's default exception handler renders `detail` alone.
        super().__init__({"detail": self.default_detail, "code": self.default_code})


class DuplicatePriorityError(APIException):
    """Raised where a flag's segment overrides would end up sharing a priority."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Segment overrides must not share a priority."


class SegmentOverrideNotFoundError(NotFound):
    """Raised where a flag serves a segment nothing of its own."""

    default_detail = "Segment override not found."
