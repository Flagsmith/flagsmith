from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware.query_params import RejectNulByteQueryParamsMiddleware


def test_reject_nul_byte_query_params_middleware__nul_byte_in_query_param__returns_bad_request(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker, rf: RequestFactory
):
    # Given
    mocked_get_response = mocker.MagicMock()
    request = rf.get(
        "/api/v1/environments/some-key/identities/", {"identifier": "foo\x00bar"}
    )

    middleware = RejectNulByteQueryParamsMiddleware(mocked_get_response)

    # When
    response = middleware(request)

    # Then
    assert response.status_code == 400
    mocked_get_response.assert_not_called()


def test_reject_nul_byte_query_params_middleware__no_nul_byte__calls_get_response(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker, rf: RequestFactory
):
    # Given
    a_response = HttpResponse()
    mocked_get_response = mocker.MagicMock(return_value=a_response)
    request = rf.get(
        "/api/v1/environments/some-key/identities/", {"identifier": "foobar"}
    )

    middleware = RejectNulByteQueryParamsMiddleware(mocked_get_response)

    # When
    response = middleware(request)

    # Then
    assert response is a_response
    mocked_get_response.assert_called_once_with(request)


def test_reject_nul_byte_query_params_middleware__nul_byte_in_repeated_key__returns_bad_request(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker, rf: RequestFactory
):
    # Given - `identifier` is repeated; `QueryDict.values()` would only see
    # the last ("foobar"), silently missing the NUL byte in the first.
    mocked_get_response = mocker.MagicMock()
    request = rf.get(
        "/api/v1/environments/some-key/identities/?identifier=foo%00bar&identifier=foobar"
    )

    middleware = RejectNulByteQueryParamsMiddleware(mocked_get_response)

    # When
    response = middleware(request)

    # Then
    assert response.status_code == 400
    mocked_get_response.assert_not_called()
