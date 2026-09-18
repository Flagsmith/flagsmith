from typing import Any

from django.http import HttpRequest, HttpResponse
from structlog.contextvars import bind_contextvars, clear_contextvars

from api_keys.user import APIKeyUser
from environments.models import Environment
from users.models import FFAdminUser


class StructlogContextMiddleware:
    """
    Scopes structlog.contextvars to a single HTTP request and binds
    request-derived identifiers so every log event emitted during the
    request automatically carries them.

    Bindings (best-effort, only what the middleware can derive):
      - user.id           — from request.user.uuid (FFAdminUser only)
      - organisation.id   — from request.user (FFAdminUser or APIKeyUser)
      - project.id        — from project_pk URL kwarg
      - environment.id    — from environment_api_key URL kwarg (cached lookup)

    Cleanup runs in `finally` to prevent Gunicorn's long-lived gthread
    workers from leaking one request's bindings into the next.
    """

    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            self._bind_user_and_organisation(request)
            return self.get_response(request)  # type: ignore[no-any-return]
        finally:
            clear_contextvars()

    def process_view(
        self,
        request: HttpRequest,
        view_func: Any,
        view_args: tuple[Any, ...],
        view_kwargs: dict[str, Any],
    ) -> None:
        project_pk = view_kwargs.get("project_pk")
        if project_pk is not None:
            bind_contextvars(project__id=project_pk)

        environment_api_key = view_kwargs.get("environment_api_key")
        if environment_api_key is not None:
            environment = Environment.get_from_cache(environment_api_key)
            if environment is not None:
                bind_contextvars(environment__id=environment.id)

    @staticmethod
    def _bind_user_and_organisation(request: HttpRequest) -> None:
        user = getattr(request, "user", None)
        if user is None or not getattr(user, "is_authenticated", False):
            return

        if isinstance(user, FFAdminUser):
            bind_contextvars(user__id=str(user.uuid))
            first_org = user.organisations.first()
            if first_org is not None:
                bind_contextvars(organisation__id=first_org.id)
        elif isinstance(user, APIKeyUser):
            bind_contextvars(organisation__id=user.key.organisation_id)
