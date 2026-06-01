from unittest.mock import MagicMock

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from oauth2_metadata.authentication import OAuth2BearerTokenAuthentication


@pytest.mark.parametrize(
    "auth_header",
    [
        "",
        "Token some-token",
        "Basic dXNlcjpwYXNz",
        "Api-Key master-api-key",
    ],
)
def test_authenticate__non_bearer_header__returns_none(
    auth_header: str,
) -> None:
    # Given
    factory = APIRequestFactory()
    request = Request(factory.get("/", HTTP_AUTHORIZATION=auth_header))
    auth = OAuth2BearerTokenAuthentication()

    # When
    result = auth.authenticate(request)

    # Then
    assert result is None


def test_authenticate__bearer_header__delegates_to_dot(
    mocker: MagicMock,
) -> None:
    # Given
    mock_user = MagicMock()
    mocker.patch(
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication.authenticate",
        return_value=(mock_user, "test-token"),
    )
    request = Request(
        APIRequestFactory().get("/", HTTP_AUTHORIZATION="Bearer test-token")
    )
    auth = OAuth2BearerTokenAuthentication()

    # When
    result = auth.authenticate(request)

    # Then
    assert result == (mock_user, "test-token")
