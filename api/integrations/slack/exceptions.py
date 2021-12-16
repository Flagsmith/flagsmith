from rest_framework.exceptions import APIException


class InValidStateError(APIException):
    status_code = 400
    default_detail = "State mismatch upon authorization completion. Try new request."
