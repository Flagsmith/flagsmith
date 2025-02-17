from datetime import datetime
from typing import Optional, Type

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36

from custom_auth.mfa.backends.application import CustomApplicationBackend
from custom_auth.mfa.trench.models import MFAMethod

User: AbstractUser = get_user_model()


class UserTokenGenerator(PasswordResetTokenGenerator):
    """
    Custom token generator:
        - user pk in token
        - expires after 15 minutes
        - longer hash (40 instead of 20)
    """

    KEY_SALT = "django.contrib.auth.tokens.PasswordResetTokenGenerator"
    SECRET = settings.SECRET_KEY
    EXPIRY_TIME = 60 * 15

    def make_token(self, user: User) -> str:
        return self._make_token_with_timestamp(user, int(datetime.now().timestamp()))

    def check_token(self, user: User, token: str) -> Optional[User]:
        user_model = get_user_model()
        try:
            token = str(token)
            user_pk, ts_b36, token_hash = token.rsplit("-", 2)
            ts = base36_to_int(ts_b36)
            user = user_model._default_manager.get(pk=user_pk)
        except (ValueError, TypeError, user_model.DoesNotExist):
            return None

        if (datetime.now().timestamp() - ts) > self.EXPIRY_TIME:
            return None  # pragma: no cover

        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            return None  # pragma: no cover

        return user

    def _make_token_with_timestamp(self, user: User, timestamp: int, **kwargs) -> str:
        ts_b36 = int_to_base36(timestamp)
        token_hash = salted_hmac(
            self.KEY_SALT,
            self._make_hash_value(user, timestamp),
            secret=self.SECRET,
        ).hexdigest()
        return f"{user.pk}-{ts_b36}-{token_hash}"  # type: ignore[attr-defined]


user_token_generator = UserTokenGenerator()


def get_mfa_model() -> Type[MFAMethod]:
    return MFAMethod


def get_mfa_handler(mfa_method: MFAMethod) -> CustomApplicationBackend:
    conf = settings.TRENCH_AUTH["MFA_METHODS"]["app"]
    mfa_handler = CustomApplicationBackend(mfa_method=mfa_method, config=conf)
    return mfa_handler
