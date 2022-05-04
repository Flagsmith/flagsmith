from rest_framework import status
from rest_framework.exceptions import APIException


class TraitPersistenceError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
