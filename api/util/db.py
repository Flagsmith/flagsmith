from collections.abc import Iterator
from contextlib import contextmanager
from typing import TypeVar

from django.db import (
    DEFAULT_DB_ALIAS,
    OperationalError,
    close_old_connections,
    connections,
    transaction,
)
from django.db.models import QuerySet
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_DELETE,
    BEFORE_DELETE,
    LifecycleModelMixin,
)
from psycopg2.errors import QueryCanceled

from core.exceptions import StatementTimeoutError

M = TypeVar("M", bound=LifecycleModelMixin)


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
    instances = list(queryset)
    for instance in instances:
        instance._run_hooked_methods(BEFORE_DELETE)
    yield queryset
    for instance in instances:
        instance._run_hooked_methods(AFTER_DELETE)


@contextmanager
def with_statement_timeout(
    milliseconds: int,
    using: str = DEFAULT_DB_ALIAS,
) -> Iterator[None]:
    """
    Cancel any query in the wrapped block that runs longer than `milliseconds`.

    Without this, Postgres keeps running a slow query after the client gives
    up, and retries pile more queries onto the database.
    """
    try:
        with transaction.atomic(using=using):
            with connections[using].cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = %s", [milliseconds])
            yield
    except OperationalError as exc:
        if not isinstance(exc.__cause__, QueryCanceled):
            raise
        raise StatementTimeoutError() from exc
