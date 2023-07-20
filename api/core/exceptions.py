from rest_framework import status
from rest_framework.exceptions import APIException


class ObjectsLimitReachedError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The project has reached the maximum allowed segments."
