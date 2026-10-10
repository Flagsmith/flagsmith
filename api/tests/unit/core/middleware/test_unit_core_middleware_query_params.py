from django.http import HttpResponse, QueryDict

from core.middleware.query_params import NullCharacterQueryParamMiddleware


def test_null_char_middleware__strips_null_from_query_param_values(mocker):  # type: ignore[no-untyped-def]
    # Given
    mocked_get_response = mocker.MagicMock(return_value=HttpResponse())
    mock_request = mocker.MagicMock()
    mock_request.META = {"QUERY_STRING": "identifier=test\x00value"}
    query_dict = QueryDict("identifier=test\x00value")
    mock_request.GET = query_dict

    middleware = NullCharacterQueryParamMiddleware(mocked_get_response)  # type: ignore[no-untyped-call]

    # When
    middleware(mock_request)

    # Then
    assert mock_request.GET["identifier"] == "testvalue"
    assert "\x00" not in mock_request.META["QUERY_STRING"]


def test_null_char_middleware__strips_null_from_query_param_keys(mocker):  # type: ignore[no-untyped-def]
    # Given
    mocked_get_response = mocker.MagicMock(return_value=HttpResponse())
    mock_request = mocker.MagicMock()
    mock_request.META = {"QUERY_STRING": "ident\x00ifier=test"}
    query_dict = QueryDict("ident\x00ifier=test")
    mock_request.GET = query_dict

    middleware = NullCharacterQueryParamMiddleware(mocked_get_response)  # type: ignore[no-untyped-call]

    # When
    middleware(mock_request)

    # Then
    assert "identifier" in mock_request.GET
    assert mock_request.GET["identifier"] == "test"


def test_null_char_middleware__no_null_chars__passes_through(mocker):  # type: ignore[no-untyped-def]
    # Given
    mocked_get_response = mocker.MagicMock(return_value=HttpResponse())
    mock_request = mocker.MagicMock()
    mock_request.META = {"QUERY_STRING": "identifier=testvalue"}
    original_get = QueryDict("identifier=testvalue")
    mock_request.GET = original_get

    middleware = NullCharacterQueryParamMiddleware(mocked_get_response)  # type: ignore[no-untyped-call]

    # When
    middleware(mock_request)

    # Then
    assert mock_request.GET is original_get


def test_null_char_middleware__empty_query_string__passes_through(mocker):  # type: ignore[no-untyped-def]
    # Given
    mocked_get_response = mocker.MagicMock(return_value=HttpResponse())
    mock_request = mocker.MagicMock()
    mock_request.META = {"QUERY_STRING": ""}
    original_get = QueryDict("")
    mock_request.GET = original_get

    middleware = NullCharacterQueryParamMiddleware(mocked_get_response)  # type: ignore[no-untyped-call]

    # When
    middleware(mock_request)

    # Then
    assert mock_request.GET is original_get
