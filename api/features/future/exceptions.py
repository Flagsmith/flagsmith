"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from rest_framework import status
from rest_framework.exceptions import APIException, NotFound


class DuplicatePriorityError(APIException):
    """Raised where a flag's segment overrides would end up sharing a priority."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Segment overrides must not share a priority."


class SegmentOverrideNotFoundError(NotFound):
    """Raised where a flag serves a segment nothing of its own."""

    default_detail = "Segment override not found."
