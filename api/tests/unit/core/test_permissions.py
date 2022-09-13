from core.permissions import HasMasterAPIKey


def test_has_master_api_key_return_true_if_master_api_key_is_part_of_request(rf):
    # Given
    request = rf.get("/some-endpoint")
    request.master_api_key = "some_key"
    permission = HasMasterAPIKey()

    # Then
    assert permission.has_permission(request, "") is True


def test_has_master_api_key_return_false_if_master_api_key_is_not_part_of_request(rf):
    # Given
    request = rf.get("/some-endpoint")
    permission = HasMasterAPIKey()

    # Then
    assert permission.has_permission(request, "") is False
