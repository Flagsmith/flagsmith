from rest_framework.exceptions import APIException


class DuplicateGitLabIntegration(APIException):
    status_code = 400
    default_detail = "A GitLab integration already exists for this project and repository."
