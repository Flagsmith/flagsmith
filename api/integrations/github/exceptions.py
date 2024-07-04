from rest_framework.exceptions import APIException


class DuplicateGitHubIntegration(APIException):
    status_code = 400
    default_detail = "Duplication error. The GitHub integration already created"
