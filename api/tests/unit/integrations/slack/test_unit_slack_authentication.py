import pytest
from django.core.signing import TimestampSigner
from rest_framework.exceptions import AuthenticationFailed

from integrations.slack.authentication import OauthInitAuthentication

oauth_init_authentication = OauthInitAuthentication()


def test_oauth_init_authentication_failes_if_invalid_signature_is_passed(rf):  # type: ignore[no-untyped-def]
    # Given
    request = rf.get("/url", {"signature": "invalid_signature"})
    # Then
    with pytest.raises(AuthenticationFailed):
        oauth_init_authentication.authenticate(request)  # type: ignore[no-untyped-call]


def test_oauth_init_authentication_with_valid_signature(django_user_model, rf):  # type: ignore[no-untyped-def]
    # Given
    signer = TimestampSigner()
    user = django_user_model.objects.create(username="test_user")
    request = rf.get("/url", {"signature": signer.sign(user.id)})
    # Then
    oauth_init_authentication.authenticate(request)  # type: ignore[no-untyped-call]


def test_oauth_init_authentication_failes_with_correct_error_if_no_signature_is_passed(  # type: ignore[no-untyped-def]  # noqa: E501
    rf,
):
    # Given
    request = rf.get("/url")
    # Then
    with pytest.raises(AuthenticationFailed):
        oauth_init_authentication.authenticate(request)  # type: ignore[no-untyped-call]
