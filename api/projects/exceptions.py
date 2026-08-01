from rest_framework.exceptions import APIException


class DynamoNotEnabledError(APIException):
    status_code = 400
    default_detail = "Dynamo DB is not enabled for this project"


class ProjectMigrationError(APIException):
    status_code = 400
    default_detail = "Migration is either already done or is in progress"


class TooManyIdentitiesError(APIException):
    status_code = 400
    default_detail = "Too many identities; Please contact support"


class ProjectTooLargeError(APIException):
    status_code = 400
    default_detail = "Project is too large; Please contact support"
from rest_framework import status
from rest_framework.exceptions import APIException


class SystemLimitError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "system-limit"
    default_detail = (
        "System limit exceeded. Please contact support to adjust your limits: "
        "https://docs.flagsmith.com/support#getting-in-touch"
    )


class DynamoNotEnabledError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Dynamo DB is not enabled for this project"


class ProjectMigrationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Migration is either already done or is in progress"


class TooManyIdentitiesError(SystemLimitError):
    default_detail = (
        "Too many identities. Please contact support to adjust your limits: "
        "https://docs.flagsmith.com/support#getting-in-touch"
    )


class ProjectTooLargeError(SystemLimitError):
    default_detail = (
        "Project is too large. Please contact support to adjust your limits: "
        "https://docs.flagsmith.com/support#getting-in-touch"
    )