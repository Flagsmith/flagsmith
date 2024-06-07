from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from custom_auth.mfa.trench.exceptions import MFAValidationError


class DispatchResponse(Response):
    _FIELD_DETAILS = "details"


class ErrorResponse(Response):
    _FIELD_ERROR = "error"

    def __init__(
        self,
        error: MFAValidationError,
        status: str = HTTP_400_BAD_REQUEST,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(
            data={self._FIELD_ERROR: str(error)}, status=status, *args, **kwargs
        )
