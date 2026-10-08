# Nothing imports this module yet, so its imports aren't covered either.
from rest_framework import status  # pragma: no cover
from rest_framework.exceptions import APIException  # pragma: no cover


class SystemSegmentModificationError(APIException):  # pragma: no cover
    # TODO: Not raised yet, hence the pragma. Remove it once the segment override
    # and change request APIs refuse system segment changes, and integration
    # tests cover them. https://github.com/Flagsmith/flagsmith/issues/8608
    """A user tried to change a system segment, or one of its overrides."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "system_segment_modification"
    default_detail = "System segments and their overrides can't be changed directly."
