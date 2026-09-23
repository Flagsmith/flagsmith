from rest_framework import status
from rest_framework.exceptions import APIException


class ChangeRequestsEnabledError(APIException):
    """Raised where a change can only be made by going through a change request."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "change_requests_enabled"
    default_detail = "Cannot make this change where change requests are enabled."

    def __init__(self, detail: str | None = None) -> None:
        # DRF's default exception handler renders `detail` alone.
        super().__init__(
            {"detail": detail or self.default_detail, "code": self.default_code}
        )
