from api_keys.middleware import MasterAPIKeyMiddleware


def test_MasterAPIKeyMiddleware_adds_master_api_key_object_to_request(
    master_api_key, rf, mocker
):
    # Given
    request = rf.get("/some-endpoint", HTTP_AUTHORIZATION="Api-Key " + master_api_key)
    mocked_get_response = mocker.MagicMock()
    middleware = MasterAPIKeyMiddleware(mocked_get_response)

    # When
    _ = middleware(request)

    # Then
    assert request.master_api_key.id is not None
