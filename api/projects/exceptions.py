from rest_framework.exceptions import APIException


class DynamoNotEnabledError(APIException):
    status_code = 400
    default_detail = "Dynamo DB is not enabled for this project"
