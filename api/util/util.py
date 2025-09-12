from itertools import islice
from math import ceil
from threading import Thread
from typing import Generator, Iterable, TypeVar

from django.conf import settings

T = TypeVar("T")


def postpone(function):  # type: ignore[no-untyped-def]
    def decorator(*args, **kwargs):  # type: ignore[no-untyped-def]
        if settings.ENABLE_POSTPONE_DECORATOR:  # pragma: no cover
            t = Thread(target=function, args=args, kwargs=kwargs)
            t.daemon = True
            t.start()
        else:
            return function(*args, **kwargs)

    return decorator


def iter_paired_chunks(
    iterable_1: Iterable[T],
    iterable_2: Iterable[T],
    *,
    chunk_size: int,
) -> Generator[tuple[Iterable[T], Iterable[T]], None, None]:
    """
    Iterate over two iterables in parallel, yielding chunks of combined size `chunk_size`.
    """
    iterator_1 = iter(iterable_1)
    iterator_2 = iter(iterable_2)
    chunk_1_size = ceil(chunk_size / 2)
    while True:
        chunk_1 = list(islice(iterator_1, chunk_1_size))
        chunk_2_size = chunk_size - len(chunk_1)
        chunk_2 = list(islice(iterator_2, chunk_2_size))
        if not chunk_2:
            if not chunk_1:
                break
            # iterable_2 is exhausted, but iterable_1 is not
            # let's get greedy
            chunk_1 += list(islice(iterator_1, chunk_2_size))
            chunk_1_size = chunk_size
        yield chunk_1, chunk_2


def iter_chunked_concat(
    values: list[str],
    delimiter: str,
    max_len: int,
) -> Generator[str, None, None]:
    """
    Iterate over a list of strings and yield concatenated chunks
    separated by a delimiter, ensuring that the total length of each
    chunk does not exceed `max_len`.
    """
    chunk: list[str] = []
    current_len = 0

    delimiter_len = len(delimiter)

    for value in values:
        value_len = len(value)
        if not chunk:
            # First item, no delimiter
            chunk.append(value)
            current_len = value_len
        else:
            # Calculate length if we add this string with delimiter
            added_len = delimiter_len + value_len
            if current_len + added_len <= max_len:
                chunk.append(value)
                current_len += added_len
            else:
                # Yield current chunk and start a new one
                yield delimiter.join(chunk)
                chunk = [value]
                current_len = value_len

    if chunk:
        yield delimiter.join(chunk)


def truncate(
    value: str,
    delimiter: str = "...",
    ends_len: int = 5,
) -> str:
    """
    Truncate a string by keeping the first `ends_len` and last `ends_len` characters,
    separated by a delimiter.
    """
    return delimiter.join([value[:ends_len], value[-ends_len:]])
