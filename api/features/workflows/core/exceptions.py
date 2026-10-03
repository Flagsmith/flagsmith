from rest_framework import status
from rest_framework.exceptions import APIException


class FeatureWorkflowError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ChangeRequestNotApprovedError(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST  # type: ignore[assignment]


class ChangeRequestStaleError(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST  # type: ignore[assignment]
    default_detail = (
        "This change request is out of date with changes published since it "
        "was created. Please refresh and reapply your changes."
    )


class CannotApproveOwnChangeRequest(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST  # type: ignore[assignment]


class ChangeRequestDeletionError(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST  # type: ignore[assignment]


class CannotModifyManagedSegmentError(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST  # type: ignore[assignment]
