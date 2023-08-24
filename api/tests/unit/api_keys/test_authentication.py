import pytest
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from api_keys.authentication import MasterAPIKeyAuthentication


def test_authenticate_returns_api_key_user_for_valid_key(master_api_key, rf):
    # Given
    master_api_key, key = master_api_key
    request = rf.get("/some-endpoint", HTTP_AUTHORIZATION="Api-Key " + key)

    # When
    user, _ = MasterAPIKeyAuthentication().authenticate(request)

    # Then
    assert user.key == master_api_key


def test_authenticate_returns_none_if_no_key_provider(rf):
    # Given
    request = rf.get("/some-endpoint")

    # When
    assert MasterAPIKeyAuthentication().authenticate(request) is None


def test_authenticate_raises_error_for_expired_key(rf, master_api_key):
    # Given
    master_api_key, key = master_api_key

    request = rf.get("/some-endpoint", HTTP_AUTHORIZATION="Api-Key " + key)
    master_api_key.expiry_date = timezone.now()
    master_api_key.save()

    # When
    with pytest.raises(AuthenticationFailed):
        MasterAPIKeyAuthentication().authenticate(request)

    # Then - exception was raised


def test_authenticate_raises_error_for_invalid_key(rf, db):
    # Given
    request = rf.get("/some-endpoint", HTTP_AUTHORIZATION="Api-Key something_random")

    # When
    with pytest.raises(AuthenticationFailed):
        MasterAPIKeyAuthentication().authenticate(request)

    # Then - exception was raised


def test_authenticate_raises_error_for_revoked_key(rf, master_api_key):
    # Given
    master_api_key, key = master_api_key

    request = rf.get("/some-endpoint", HTTP_AUTHORIZATION="Api-Key " + key)
    master_api_key.revoked = True
    master_api_key.save()

    # When
    with pytest.raises(AuthenticationFailed):
        MasterAPIKeyAuthentication().authenticate(request)

    # Then - exception was raised
