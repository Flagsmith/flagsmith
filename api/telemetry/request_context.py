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
from environments.models import Environment
from projects.models import Project
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

    _bind_url_entities(view.kwargs)


def _bind_url_entities(url_kwargs: dict[str, typing.Any]) -> None:
    """
    Bind the entities the request acts on, best effort, from its URL.

    These describe what the request targets, whether or not it's allowed to.
    Entities that don't exist, e.g. were deleted, aren't bound.
    """
    if (project_id := _get_id(url_kwargs, "project_pk")) is not None:
        bind_request_context(project__id=project_id)
        # NOTE: Most views load the project anyway, but in too many places
        # to reuse; this is a cheap primary key lookup. It filters by `id`, as
        # `pk` lookups include soft-deleted projects.
        organisation_id = (
            Project.objects.filter(id=project_id)
            .values_list("organisation_id", flat=True)
            .first()
        )
        if organisation_id is not None:
            bind_request_context(organisation__id=organisation_id)

    if (feature_id := _get_id(url_kwargs, "feature_pk")) is not None:
        bind_request_context(feature__id=feature_id)

    if environment_api_key := url_kwargs.get("environment_api_key"):
        environment_ids = (
            Environment.objects.filter(api_key=environment_api_key)
            .values_list("id", "project_id", "project__organisation_id")
            .first()
        )
        if environment_ids is not None:
            environment_id, project_id, organisation_id = environment_ids
            bind_request_context(
                environment__id=environment_id,
                project__id=project_id,
                organisation__id=organisation_id,
            )


def _get_id(url_kwargs: dict[str, typing.Any], name: str) -> int | None:
    value = url_kwargs.get(name)
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        return int(value)
    return None


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
