from rest_framework import status
from rest_framework.exceptions import APIException


class GitLabApiUnreachable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "GitLab API is unreachable"
    default_code = "gitlab_api_unreachable"
