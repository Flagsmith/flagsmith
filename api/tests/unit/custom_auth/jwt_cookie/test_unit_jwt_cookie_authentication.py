from typing import Type
from unittest.mock import MagicMock, patch

import pytest
from rest_framework.request import Request
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.tokens import Token

from custom_auth.jwt_cookie.authentication import JWTCookieAuthentication
from custom_auth.jwt_cookie.constants import JWT_SLIDING_COOKIE_KEY
from users.models import FFAdminUser


def test_authenticate_without_cookie() -> None:
    # Given
    auth = JWTCookieAuthentication()
    request = MagicMock(spec=Request)
    request.COOKIES = {}

    # When
    result = auth.authenticate(request)

    # Then
    assert result is None


def test_authenticate_valid_cookie() -> None:
    # Given
    auth = JWTCookieAuthentication()
    request = MagicMock(spec=Request)
    raw_token = "valid_token"
    request.COOKIES = {JWT_SLIDING_COOKIE_KEY: raw_token}

    validated_token = MagicMock(spec=Token)
    user = MagicMock(spec=FFAdminUser)

    # Mock the validation and user retrieval
    with patch.object(
        auth, "get_validated_token", return_value=validated_token
    ) as mock_validate:
        with patch.object(auth, "get_user", return_value=user) as mock_get_user:
            # When
            result = auth.authenticate(request)

            # Then
            assert result == (user, validated_token)
            mock_validate.assert_called_once_with(raw_token)
            mock_get_user.assert_called_once_with(validated_token)


@pytest.mark.parametrize(
    "exception_class", [InvalidToken, TokenError, AuthenticationFailed]
)
def test_authenticate_invalid_cookie(exception_class: Type[Exception]) -> None:
    # Given
    auth = JWTCookieAuthentication()
    request = MagicMock(spec=Request)
    raw_token = "invalid_token"
    request.COOKIES = {JWT_SLIDING_COOKIE_KEY: raw_token}

    # Test that no further exceptions are raised if the token is invalid in any way
    with patch.object(
        auth, "get_validated_token", side_effect=exception_class("Error")
    ):
        # When
        result = auth.authenticate(request)

        # Then
        assert result is None
