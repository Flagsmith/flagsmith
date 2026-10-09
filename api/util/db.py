from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, TypeVar

from django.db import close_old_connections
from django.db.models import Model, QuerySet
from django_lifecycle import AFTER_DELETE, BEFORE_DELETE  # type: ignore[import-untyped]

M = TypeVar("M", bound=Model)


@contextmanager
def closing_stale_connections() -> Iterator[None]:
    """
    Close any stale DB connections when the wrapped block exits.

    Intended for blocks that may hold a DB connection idle for long enough
    that the DB server (or an intermediate proxy) terminates it — e.g. an
    HTTP call to a slow third-party API preceding a write phase.
    """
    try:
        yield
    finally:
        close_old_connections()


@contextmanager
def with_delete_hooks(queryset: QuerySet[M]) -> Iterator[QuerySet[M]]:
    """Run the django-lifecycle delete hooks of the instances a queryset deletes.

    Deleting a queryset, rather than each instance, skips those hooks.

    TODO: Stop running private hooks after
    https://github.com/Flagsmith/flagsmith/issues/7315
    """
    instances: list[Any] = list(queryset)
    for instance in instances:
        instance._run_hooked_methods(BEFORE_DELETE)
    yield queryset
    for instance in instances:
        instance._run_hooked_methods(AFTER_DELETE)
