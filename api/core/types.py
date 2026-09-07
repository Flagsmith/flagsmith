from rest_framework.request import Request

from api_keys.user import APIKeyUser
from users.models import FFAdminUser


class AuthenticatedRequest(Request):
    """A request a permission class has already vetted as authenticated.

    Annotate a view method with this in place of `Request` to narrow `request.user`,
    which DRF types as possibly anonymous, wherever `IsAuthenticated` guarantees a user.
    """

    # Narrowing an attribute in a subclass is unsound in the general case, so mypy
    # rejects it. This class is annotation-only and never instantiated, so the
    # narrowing is safe: it only describes a request a permission class has already
    # validated. Remove if DRF ever makes Request generic over its user type.
    user: FFAdminUser | APIKeyUser  # type: ignore[assignment]
