import pytest

from util.util import batched, iter_chunked_concat, iter_paired_chunks


def test_iter_paired_chunks__both_empty__returns_empty_list() -> None:
    # Given / When
    result: list[object] = list(iter_paired_chunks([], [], chunk_size=1))

    # Then
    assert result == []


def test_iter_paired_chunks__first_empty__chunks_second_only() -> None:
    # Given / When
    result = list(iter_paired_chunks([], [1, 2, 3], chunk_size=1))

    # Then
    assert result == [
        ([], [1]),
        ([], [2]),
        ([], [3]),
    ]


def test_iter_paired_chunks__second_empty__chunks_first_only() -> None:
    # Given / When
    result = list(iter_paired_chunks([1, 2, 3], [], chunk_size=1))

    # Then
    assert result == [
        ([1], []),
        ([2], []),
        ([3], []),
    ]


def test_iter_paired_chunks__first_shorter__distributes_across_chunks() -> None:
    # Given / When
    result = list(iter_paired_chunks([1, 2, 3], [4, 5, 6, 7, 8], chunk_size=3))

    # Then
    assert result == [
        ([1, 2], [4]),
        ([3], [5, 6]),
        ([], [7, 8]),
    ]


def test_iter_paired_chunks__second_shorter__distributes_across_chunks() -> None:
    # Given / When
    result = list(iter_paired_chunks([1, 2, 3, 4, 5], [6, 7, 8], chunk_size=3))

    # Then
    assert result == [
        ([1, 2], [6]),
        ([3, 4], [7]),
        ([5], [8]),
    ]


def test_iter_paired_chunks__same_length__distributes_across_chunks() -> None:
    # Given / When
    result = list(iter_paired_chunks([1, 2, 3], [4, 5, 6], chunk_size=3))

    # Then
    assert result == [
        ([1, 2], [4]),
        ([3], [5, 6]),
    ]


@pytest.mark.parametrize(
    "values, delimiter, max_len, expected_result",
    [
        # Basic chunking
        (
            ["alpha", "beta", "gamma", "delta", "epsilon"],
            ",",
            15,
            ["alpha,beta", "gamma,delta", "epsilon"],
        ),
        # One string longer than max_len
        (
            ["supercalifragilisticexpialidocious"],
            ",",
            10,
            ["supercalifragilisticexpialidocious"],
        ),
        # Delimiter length affects fit
        (["a", "b", "c", "d"], "::", 5, ["a::b", "c::d"]),
        # Chunk fits exactly with delimiter
        (["abc", "def"], "-", 7, ["abc-def"]),
        # Empty list
        ([], ",", 10, []),
        # One string exceeds max_len, others do not
        (
            ["tiny", "thisisaverylongword", "ok"],
            ",",
            10,
            ["tiny", "thisisaverylongword", "ok"],
        ),
        # Single short string
        (["abc"], ",", 10, ["abc"]),
        # All strings fit into one chunk
        (["a", "b", "c"], ",", 5, ["a,b,c"]),
    ],
)
def test_iter_chunked_concat__various_inputs__returns_expected_chunks(
    values: list[str],
    delimiter: str,
    max_len: int,
    expected_result: list[str],
) -> None:
    # Given / When
    result = iter_chunked_concat(
        values=values,
        delimiter=delimiter,
        max_len=max_len,
    )

    # Then
    assert list(result) == expected_result


def test_batched__empty_iterable__yields_nothing() -> None:
    # Given an empty iterable
    # When batched
    # Then no batches are yielded
    assert list(batched([], 3)) == []


def test_batched__exact_multiple__yields_full_batches() -> None:
    # Given an iterable whose length is a multiple of the batch size
    # When batched
    # Then every batch is full
    assert list(batched(range(6), 2)) == [[0, 1], [2, 3], [4, 5]]


def test_batched__remainder__yields_smaller_final_batch() -> None:
    # Given an iterable whose length isn't a multiple of the batch size
    # When batched
    # Then the final batch carries the remainder
    assert list(batched([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
