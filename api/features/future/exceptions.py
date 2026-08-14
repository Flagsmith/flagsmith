"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from collections.abc import Sequence

from django.utils.text import get_text_list
from rest_framework import status
from rest_framework.exceptions import APIException

from segments.models import Segment


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

    def __init__(self, segments: Sequence[Segment]) -> None:
        conflicted = get_text_list(
            [f"{segment.id} ({segment.name})" for segment in segments],
            "and",
        )
        super().__init__(
            f"The overrides for segments {conflicted} are in conflict; "
            "provide explicit priority values."
        )
