from collections.abc import Iterator
from contextlib import contextmanager

from django.db import close_old_connections


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
