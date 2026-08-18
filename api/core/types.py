from rest_framework.request import Request

from api_keys.user import APIKeyUser
from users.models import FFAdminUser


class AuthenticatedRequest(Request):
    """A request a permission class has already vetted as authenticated.

    Annotate a view method with this in place of `Request` to narrow `request.user`,
    which DRF types as possibly anonymous, wherever `IsAuthenticated` guarantees a user.
    """

    user: FFAdminUser | APIKeyUser
