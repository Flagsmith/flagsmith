from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import ValidationError


class MethodHandlerMissingError(ImproperlyConfigured):
    def __init__(self, method_name: str) -> None:
        super().__init__(f"Missing handler in {method_name} configuration.")


class MFAValidationError(ValidationError):
    def __str__(self) -> str:
        return ", ".join(detail for detail in self.detail)


class CodeInvalidOrExpiredError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_("Code invalid or expired."),
            code="code_invalid_or_expired",
        )


class OTPCodeMissingError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(detail=_("OTP code not provided."), code="otp_code_missing")


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


class DeactivationOfPrimaryMFAMethodError(MFAValidationError):
    def __init__(self) -> None:
        super().__init__(
            detail=_(
                "Deactivation of MFA method that is set as primary is not allowed."
            ),
            code="deactivation_of_primary",
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
