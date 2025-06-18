from rest_framework import status
from rest_framework.exceptions import APIException


class ReleasePipelineError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class InvalidPipelineStateError(ReleasePipelineError):
    status_code = status.HTTP_400_BAD_REQUEST  # type: ignore[assignment]
