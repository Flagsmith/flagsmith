from rest_framework.exceptions import APIException


class DuplicateGitLabIntegration(APIException):
    status_code = 400
    default_detail = "Duplication error. The GitLab integration already created"
