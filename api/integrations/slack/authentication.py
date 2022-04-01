from contextlib import suppress

from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import BadSignature, TimestampSigner
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.models import FFAdminUser


class OauthInitAuthentication(BaseAuthentication):
    """
    Custom authentication class to use signed user_id present in query params
    """

    def authenticate(self, request):
        signer = TimestampSigner()
        with suppress(BadSignature, ObjectDoesNotExist):
            signature = request.GET.get("signature")
            if not signature:
                raise AuthenticationFailed(
                    "Authentication credentials were not provided."
                )
            user_id = signer.unsign(signature, max_age=30)
            user = FFAdminUser.objects.get(id=user_id)
            return user, None
        raise AuthenticationFailed("No such user")
