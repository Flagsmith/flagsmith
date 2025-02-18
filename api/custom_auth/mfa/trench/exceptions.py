from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ValidationError


class MFAValidationError(ValidationError):
    def __str__(self) -> str:
        return ", ".join(detail for detail in self.detail)  # type: ignore[misc]


class CodeInvalidOrExpiredError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("Code invalid or expired."),
            code="code_invalid_or_expired",
        )


class MFAMethodDoesNotExistError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("Requested MFA method does not exist."),
            code="mfa_method_does_not_exist",
        )


class MFAMethodAlreadyActiveError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("MFA method already active."),
            code="method_already_active",
        )


class MFANotEnabledError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(detail=_("2FA is not enabled."), code="not_enabled")


class InvalidTokenError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(detail=_("Invalid or expired token."), code="invalid_token")


class InvalidCodeError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(detail=_("Invalid or expired code."), code="invalid_code")
