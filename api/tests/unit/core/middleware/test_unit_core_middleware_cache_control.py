from core.middleware.cache_control import NeverCacheMiddleware
from django.http import HttpResponse


def test_NoCacheMiddleware_adds_cache_control_headers(mocker):
    # Given
    a_response = HttpResponse()
    mocked_get_response = mocker.MagicMock(return_value=a_response)
    mock_request = mocker.MagicMock()

    middleware = NeverCacheMiddleware(mocked_get_response)

    # When
    response = middleware(mock_request)

    # Then
    assert (
        response.headers["Cache-Control"]
        == "max-age=0, no-cache, no-store, must-revalidate, private"
    )
    assert response.headers["Pragma"] == "no-cache"
