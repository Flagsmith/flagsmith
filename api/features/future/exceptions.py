"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from rest_framework import status
from rest_framework.exceptions import APIException


class ChangeRequestsEnabledError(APIException):
    """Raised where a flag can only be changed by going through a change request."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = (
        "Cannot update flags in an environment with change requests enabled."
    )
