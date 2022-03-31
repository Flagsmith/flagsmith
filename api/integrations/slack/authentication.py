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
        logger.debug("OauthInitAuthentication authenticate called")
        signer = TimestampSigner()
        try:
            signature = request.GET.get("signature")
            if not signature:
                raise AuthenticationFailed(
                    "Authentication credentials were not provided."
                )
            user_id = signer.unsign(signature, max_age=30)
            user = FFAdminUser.objects.get(id=user_id)

            logger.debug(f"OauthInitAuthentication normal return with user {user}")
            return user, None
        except (BadSignature, ObjectDoesNotExist):
            logger.debug("OauthInitAuthentication raising an exception")
            raise AuthenticationFailed("No such user")
