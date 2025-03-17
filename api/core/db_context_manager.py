from contextlib import contextmanager
from typing import Iterator

from core.db_context import disable_read_replicas, enable_read_replicas


@contextmanager
def read_replicas() -> Iterator[None]:
    try:
        enable_read_replicas()
        yield
    finally:
        disable_read_replicas()
