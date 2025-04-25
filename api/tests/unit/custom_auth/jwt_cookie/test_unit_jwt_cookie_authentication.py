from typing import Type

import pytest
from pytest_mock import MockerFixture
from rest_framework.request import Request
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
from rest_framework_simplejwt.tokens import Token

from custom_auth.jwt_cookie.authentication import JWTCookieAuthentication
from custom_auth.jwt_cookie.constants import (
    ACCESS_TOKEN_COOKIE_KEY,
    REFRESH_TOKEN_COOKIE_KEY,
)
from users.models import FFAdminUser


def test_authenticate_without_cookie(mocker: MockerFixture) -> None:
    # Given
    auth = JWTCookieAuthentication()
    request = mocker.MagicMock(spec=Request)
    request.COOKIES = {}

    # When
    result = auth.authenticate(request)

    # Then
    assert result is None


def test_authenticate_valid_cookie(mocker: MockerFixture) -> None:
    # Given
    auth = JWTCookieAuthentication()
    request = mocker.MagicMock(spec=Request)
    raw_access_token = "valid_access_token"
    request.COOKIES = {ACCESS_TOKEN_COOKIE_KEY: raw_access_token}

    validated_token = mocker.MagicMock(spec=Token)
    user = mocker.MagicMock(spec=FFAdminUser)

    # Mock the validation and user retrieval
    mock_validate = mocker.patch.object(
        auth, "get_validated_token", return_value=validated_token
    )
    mock_get_user = mocker.patch.object(auth, "get_user", return_value=user)

    # When
    result = auth.authenticate(request)

    # Then
    assert result == (user, validated_token)
    mock_validate.assert_called_once_with(raw_access_token)
    mock_get_user.assert_called_once_with(validated_token)


@pytest.mark.parametrize(
    "exception_class", [InvalidToken, TokenError, AuthenticationFailed]
)
def test_authenticate_invalid_cookie(
    mocker: MockerFixture,
    exception_class: Type[Exception],
) -> None:
    # Given
    auth = JWTCookieAuthentication()
    request = mocker.MagicMock(spec=Request)
    raw_invalid_access_token = "invalid_access_token"
    request.COOKIES = {ACCESS_TOKEN_COOKIE_KEY: raw_invalid_access_token}

    # Test that no further exceptions are raised if the token is invalid in any way
    mocker.patch.object(
        auth, "get_validated_token", side_effect=exception_class("Error")
    ).side_effect = exception_class("Error")

    # When
    result = auth.authenticate(request)

    # Then
    assert result is None
