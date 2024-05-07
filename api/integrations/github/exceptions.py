from rest_framework.exceptions import APIException


class DuplicateGitHubIntegration(APIException):
    status_code = 400
    default_detail = "Duplication error. The GitHub integration already created"


class InvalidInstallation(APIException):
    status_code = 410
    default_detail = "The installation is no longer valid, please delete the GitHub integration from Flagsmith or update your installation ID"  # noqa: E501
