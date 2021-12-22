from rest_framework.exceptions import APIException


class InvalidStateError(APIException):
    status_code = 400
    default_detail = "State mismatch upon authorization completion. Try new request."


class FrontEndRedirectURLNotFound(APIException):
    status_code = 400
    default_detail = "Redirect URL not found in request session"
