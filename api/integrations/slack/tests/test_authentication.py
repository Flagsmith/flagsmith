import pytest
from django.core.signing import TimestampSigner
from rest_framework.exceptions import AuthenticationFailed

from integrations.slack.authentication import OauthInitAuthentication

oauth_init_authentication = OauthInitAuthentication()


def test_oauth_init_authentication_failes_if_invalid_signature_is_passed(rf):
    # Given
    request = rf.get("/url", {"signature": "invalid_signature"})
    # Then
    with pytest.raises(AuthenticationFailed):
        oauth_init_authentication.authenticate(request)


def test_oauth_init_authentication_with_valid_signature(django_user_model, rf):
    # Given
    signer = TimestampSigner()
    user = django_user_model.objects.create(username="test_user")
    request = rf.get("/url", {"signature": signer.sign(user.id)})
    # Then
    oauth_init_authentication.authenticate(request)
