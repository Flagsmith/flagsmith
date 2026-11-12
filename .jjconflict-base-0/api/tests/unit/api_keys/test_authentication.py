import pytest
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from api_keys.authentication import MasterAPIKeyAuthentication


def test_authenticate__valid_key__returns_api_key_user(master_api_key, rf):  # type: ignore[no-untyped-def]
    # Given
    master_api_key, key = master_api_key
    request = rf.get("/some-endpoint", HTTP_AUTHORIZATION="Api-Key " + key)

    # When
    user, _ = MasterAPIKeyAuthentication().authenticate(request)  # type: ignore[no-untyped-call]

    # Then
    assert user.key == master_api_key


def test_authenticate__no_key_provided__returns_none(rf):  # type: ignore[no-untyped-def]
    # Given
    request = rf.get("/some-endpoint")

    # When
    result = MasterAPIKeyAuthentication().authenticate(request)  # type: ignore[no-untyped-call]

    # Then
    assert result is None


def test_authenticate__expired_key__raises_authentication_failed(rf, master_api_key):  # type: ignore[no-untyped-def]
    # Given
    master_api_key, key = master_api_key

    request = rf.get("/some-endpoint", HTTP_AUTHORIZATION="Api-Key " + key)
    master_api_key.expiry_date = timezone.now()
    master_api_key.save()

    # When / Then
    with pytest.raises(AuthenticationFailed):
        MasterAPIKeyAuthentication().authenticate(request)  # type: ignore[no-untyped-call]


def test_authenticate__invalid_key__raises_authentication_failed(rf, db):  # type: ignore[no-untyped-def]
    # Given
    request = rf.get("/some-endpoint", HTTP_AUTHORIZATION="Api-Key something_random")

    # When / Then
    with pytest.raises(AuthenticationFailed):
        MasterAPIKeyAuthentication().authenticate(request)  # type: ignore[no-untyped-call]


def test_authenticate__revoked_key__raises_authentication_failed(rf, master_api_key):  # type: ignore[no-untyped-def]
    # Given
    master_api_key, key = master_api_key

    request = rf.get("/some-endpoint", HTTP_AUTHORIZATION="Api-Key " + key)
    master_api_key.revoked = True
    master_api_key.save()

    # When / Then
    with pytest.raises(AuthenticationFailed):
        MasterAPIKeyAuthentication().authenticate(request)  # type: ignore[no-untyped-call]
