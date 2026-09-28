from rest_framework.request import Request
from typing_extensions import TypedDict

from api_keys.user import APIKeyUser
from users.models import FFAdminUser


class AuthenticatedRequest(Request):
    """A request a permission class has already vetted as authenticated.

    Annotate a view method with this in place of `Request` to narrow `request.user`,
    which DRF types as possibly anonymous, wherever `IsAuthenticated` guarantees a user.
    """

    user: FFAdminUser | APIKeyUser  # type: ignore[assignment]


class APIErrorDetail(TypedDict):
    """The body served where the API refuses a request."""

    code: str
    message: str
