import logging

from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import BadSignature, TimestampSigner
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.models import FFAdminUser

logger = logging.getLogger(__name__)


class OauthInitAuthentication(BaseAuthentication):
    """
    Custom authentication class to use signed user_id present in query params
    """

    def authenticate(self, request):
        signature = request.GET.get("signature")
        signer = TimestampSigner()
        logger.debug(
            f"OauthInitAuthentication authenticate called with signature {signature}"
        )
        try:
            if not signature:
                raise AuthenticationFailed(
                    "Authentication credentials were not provided."
                )
            user_id = signer.unsign(signature, max_age=30)
            user = FFAdminUser.objects.get(id=user_id)

            logger.debug(f"OauthInitAuthentication normal return with user {user}")
            return user, None
        except (BadSignature, ObjectDoesNotExist) as e:
            logger.debug("OauthInitAuthentication raising exception: %s", e)
        raise AuthenticationFailed("No such user")
