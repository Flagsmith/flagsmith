from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from freezegun import freeze_time
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import SlidingToken

from custom_auth.jwt_cookie.services import blacklist_user_tokens
from users.models import FFAdminUser


def test_blacklist_user_tokens__outstanding_tokens__blacklists_only_user_tokens(
    staff_user: FFAdminUser,
    admin_user: FFAdminUser,
) -> None:
    # Given
    SlidingToken.for_user(staff_user)
    SlidingToken.for_user(staff_user)
    SlidingToken.for_user(admin_user)

    # When
    blacklist_user_tokens(staff_user)

    # Then
    assert BlacklistedToken.objects.filter(token__user=staff_user).count() == 2
    assert not BlacklistedToken.objects.filter(token__user=admin_user).exists()


def test_blacklist_user_tokens__expired_token__skips_token(
    staff_user: FFAdminUser,
) -> None:
    # Given
    SlidingToken.for_user(staff_user)
    token_lifetime = settings.SIMPLE_JWT["SLIDING_TOKEN_LIFETIME"]

    # When
    with freeze_time(timezone.now() + token_lifetime + timedelta(seconds=1)):
        blacklist_user_tokens(staff_user)

    # Then
    assert not BlacklistedToken.objects.exists()
