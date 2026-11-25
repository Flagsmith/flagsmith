"""
Describe API requests with Flagsmith-specific request context.

`common.core.request_context.RequestContextMiddleware` scopes request context
to the request, and binds its route. What the request acts on, and who makes
it, is only known once DRF has authenticated the request inside the view, so
it's bound from there.
"""

import functools
import typing

from common.core.request_context import bind_request_context
from rest_framework.request import Request
from rest_framework.views import APIView

from api_keys.user import APIKeyUser
from telemetry.mappers import map_view_kwargs_to_resolved_ids
from telemetry.services import get_resolved_ids
from users.models import FFAdminUser


def bind_api_request_context(request: Request, view: APIView) -> None:
    """Bind what's known about `request` once DRF has authenticated it."""
    user = request.user
    if isinstance(user, FFAdminUser):
        bind_request_context(user__id=str(user.uuid))
    elif getattr(user, "is_master_api_key_user", False):
        # NOTE: `isinstance` can't tell `APIKeyUser`s apart, see `UserABC`.
        # Master API keys aren't users, so don't identify them as such; but
        # they belong to exactly one organisation.
        api_key_user = typing.cast(APIKeyUser, user)
        bind_request_context(organisation__id=api_key_user.key.organisation_id)

    resolved_ids = get_resolved_ids(map_view_kwargs_to_resolved_ids(view.kwargs))
    resolved_ids.pop("environment__api_key", None)
    bind_request_context(**resolved_ids)


def install() -> None:
    """
    Bind API request context to every DRF view's request on authentication.

    API requests, e.g. authenticated by token or master API key, are
    authenticated by DRF inside the view, so a middleware can't tell who makes
    them. DRF has no hook for authenticated requests, and views extend
    `APIView` directly, so wrap `APIView.perform_authentication`, which every
    view runs before checking permissions.
    """
    perform_authentication = APIView.perform_authentication

    @functools.wraps(perform_authentication)
    def _perform_authentication(self: APIView, request: Request) -> None:
        perform_authentication(self, request)
        bind_api_request_context(request, self)

    setattr(
        APIView,
        "perform_authentication",
        typing.cast(typing.Any, _perform_authentication),
    )
