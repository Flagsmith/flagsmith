from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from custom_auth.mfa.trench.exceptions import MFAValidationError


class DispatchResponse(Response):
    _FIELD_DETAILS = "details"


class ErrorResponse(Response):
    _FIELD_ERROR = "error"

    def __init__(  # type: ignore[no-untyped-def]
        self,
        error: MFAValidationError,
        status: str = HTTP_400_BAD_REQUEST,  # type: ignore[assignment]
        *args,
        **kwargs,
    ) -> None:
        super().__init__(  # type: ignore[misc]
            data={self._FIELD_ERROR: str(error)},
            status=status,  # type: ignore[arg-type]
            *args,
            **kwargs,
        )
