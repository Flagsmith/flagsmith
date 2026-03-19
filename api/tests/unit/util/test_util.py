import pytest

from util.util import iter_chunked_concat, iter_paired_chunks


def test_iter_paired_chunks__both_empty__returns_empty_list() -> None:  # type: ignore[no-untyped-def]
    # Given / When
    result = list(iter_paired_chunks([], [], chunk_size=1))

    # Then
    assert result == []


def test_iter_paired_chunks__first_empty__chunks_second_only() -> None:  # type: ignore[no-untyped-def]
    # Given / When
    result = list(iter_paired_chunks([], [1, 2, 3], chunk_size=1))

    # Then
    assert result == [
        ([], [1]),
        ([], [2]),
        ([], [3]),
    ]


def test_iter_paired_chunks__second_empty__chunks_first_only() -> None:  # type: ignore[no-untyped-def]
    # Given / When
    result = list(iter_paired_chunks([1, 2, 3], [], chunk_size=1))

    # Then
    assert result == [
        ([1], []),
        ([2], []),
        ([3], []),
    ]


def test_iter_paired_chunks__first_shorter__distributes_across_chunks() -> None:  # type: ignore[no-untyped-def]
    # Given / When
    result = list(iter_paired_chunks([1, 2, 3], [4, 5, 6, 7, 8], chunk_size=3))

    # Then
    assert result == [
        ([1, 2], [4]),
        ([3], [5, 6]),
        ([], [7, 8]),
    ]


def test_iter_paired_chunks__second_shorter__distributes_across_chunks() -> None:  # type: ignore[no-untyped-def]
    # Given / When
    result = list(iter_paired_chunks([1, 2, 3, 4, 5], [6, 7, 8], chunk_size=3))

    # Then
    assert result == [
        ([1, 2], [6]),
        ([3, 4], [7]),
        ([5], [8]),
    ]


def test_iter_paired_chunks__same_length__distributes_across_chunks() -> None:  # type: ignore[no-untyped-def]
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
