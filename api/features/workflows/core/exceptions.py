from rest_framework import status
from rest_framework.exceptions import APIException


class FeatureWorkflowError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ChangeRequestNotApprovedError(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST  # type: ignore[assignment]


class CannotApproveOwnChangeRequest(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST  # type: ignore[assignment]


class ChangeRequestDeletionError(FeatureWorkflowError):
    status_code = status.HTTP_400_BAD_REQUEST  # type: ignore[assignment]


class ChangeRequestConflictError(FeatureWorkflowError):
    status_code = status.HTTP_409_CONFLICT  # type: ignore[assignment]
    default_code = "change_request_conflict"
    default_detail = (
        "This change request conflicts with changes that were published since "
        "it was created. Refresh the change request, or set ignore_conflicts to "
        "commit it anyway."
    )
