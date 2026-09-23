from rest_framework import status
from rest_framework.exceptions import APIException


class TokenExchangeError(APIException):
    """Base error for OIDC token exchange rejections, rendered by DRF's
    exception handler.
    """

    status_code: int = status.HTTP_401_UNAUTHORIZED
    default_detail = "Token validation failed."
    default_code = "token_exchange_failed"


class InvalidTokenError(TokenExchangeError):
    default_code = "invalid_token"


class NoMatchingTrustRelationshipError(TokenExchangeError):
    default_detail = "No trust relationship matches this token."
    default_code = "no_matching_trust_relationship"
