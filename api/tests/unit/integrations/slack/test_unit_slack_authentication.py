import pytest
from django.core.signing import TimestampSigner
from rest_framework.exceptions import AuthenticationFailed

from integrations.slack.authentication import OauthInitAuthentication

oauth_init_authentication = OauthInitAuthentication()


def test_oauth_init_authentication__invalid_signature__raises_authentication_failed(rf):  # type: ignore[no-untyped-def]
    # Given
    request = rf.get("/url", {"signature": "invalid_signature"})
    # When / Then
    with pytest.raises(AuthenticationFailed):
        oauth_init_authentication.authenticate(request)  # type: ignore[no-untyped-call]


def test_oauth_init_authentication__valid_signature__authenticates_successfully(
    django_user_model, rf
):  # type: ignore[no-untyped-def]
    # Given
    signer = TimestampSigner()
    user = django_user_model.objects.create(username="test_user")
    request = rf.get("/url", {"signature": signer.sign(user.id)})
    # When / Then
    oauth_init_authentication.authenticate(request)  # type: ignore[no-untyped-call]


def test_oauth_init_authentication__no_signature__raises_authentication_failed(  # type: ignore[no-untyped-def]
    rf,
):
    # Given
    request = rf.get("/url")
    # When / Then
    with pytest.raises(AuthenticationFailed):
        oauth_init_authentication.authenticate(request)  # type: ignore[no-untyped-call]
