from itertools import islice
from math import ceil
from threading import Thread
from typing import Generator, Iterable, TypeVar

T = TypeVar("T")


def postpone(function):
    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

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
