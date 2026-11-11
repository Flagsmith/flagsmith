from rest_framework import status
from rest_framework.exceptions import APIException


class FeatureHealthWebhookPayloadInvalidError(APIException):
    """Raised where a feature health provider payload fails validation."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "invalid_payload"
    default_detail = "Invalid feature health webhook payload."

    def __init__(self, errors: list[dict[str, str]]) -> None:
        # DRF's default exception handler renders `detail` alone.
        super().__init__(
            {
                "detail": self.default_detail,
                "code": self.default_code,
                "errors": errors,
            }
        )


class FeatureHealthEventsNotCreatedError(APIException):
    """Raised where a valid feature health provider payload yields no events,
    e.g. because none of its features exist in the provider's project."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "no_events_created"
    default_detail = "No feature health events were created."

    def __init__(self, detail: str | None = None) -> None:
        # DRF's default exception handler renders `detail` alone.
        super().__init__(
            {"detail": detail or self.default_detail, "code": self.default_code}
        )
