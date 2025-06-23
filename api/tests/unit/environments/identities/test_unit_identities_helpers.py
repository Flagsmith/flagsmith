import itertools
from unittest import mock

from environments.identities.helpers import (
    get_hashed_percentage_for_object_ids,
)


def test_get_hashed_percentage_for_object_ids_is_number_between_0_inc_and_1_exc():  # type: ignore[no-untyped-def]
    assert 1 > get_hashed_percentage_for_object_ids([12, 93]) >= 0


def test_get_hashed_percentage_for_object_ids_is_the_same_each_time():  # type: ignore[no-untyped-def]
    # Given
    object_ids = [30, 73]

    # When
    result_1 = get_hashed_percentage_for_object_ids(object_ids)
    result_2 = get_hashed_percentage_for_object_ids(object_ids)

    # Then
    assert result_1 == result_2


def test_percentage_value_is_unique_for_different_identities():  # type: ignore[no-untyped-def]
    # Given
    first_object_ids = [14, 106]
    second_object_ids = [53, 200]

    # When
    result_1 = get_hashed_percentage_for_object_ids(first_object_ids)
    result_2 = get_hashed_percentage_for_object_ids(second_object_ids)

    # Then
    assert result_1 != result_2


def test_get_hashed_percentage_for_object_ids_should_be_evenly_distributed():  # type: ignore[no-untyped-def]
    """
    This test checks if the percentage value returned by the helper function returns
    evenly distributed values.

    Note that since it's technically random, it's not guaranteed to pass every time,
    however, it should pass 99/100 times. It will likely be more accurate by increasing
    the test_sample value and / or decreasing the num_test_buckets value.
    """
    test_sample = 500  # number of ids to sample in each list
    num_test_buckets = 50  # split the sample into 'buckets' to check that the values are evenly distributed
    test_bucket_size = int(test_sample / num_test_buckets)
    error_factor = 0.1

    # Given
    object_id_pairs = itertools.product(range(test_sample), range(test_sample))

    # When
    values = sorted(
        get_hashed_percentage_for_object_ids(pair) for pair in object_id_pairs
    )

    # Then
    for i in range(num_test_buckets):
        bucket_start = i * test_bucket_size
        bucket_end = (i + 1) * test_bucket_size
        bucket_value_limit = min(
            (i + 1) / num_test_buckets + error_factor * ((i + 1) / num_test_buckets),
            1,
        )

        assert all(
            [value <= bucket_value_limit for value in values[bucket_start:bucket_end]]
        )


@mock.patch("environments.identities.helpers.hashlib")
def test_get_hashed_percentage_does_not_return_1(mock_hashlib):  # type: ignore[no-untyped-def]
    """
    Quite complex test to ensure that the function will never return 1.

    To achieve this, we mock the hashlib module to return a magic mock so that we can
    subsequently mock the hexdigest method to return known strings. These strings are
    chosen such that they can be converted (via `int(s, base=16)`) to known integers.
    """

    # Given
    object_ids = [12, 93]

    # -- SETTING UP THE MOCKS --
    # hash strings specifically created to return specific values when converted to
    # integers via int(s, base=16). Note that the reverse function was created
    # courtesy of https://code.i-harness.com/en/q/1f7c41
    hash_string_to_return_1 = "270e"
    hash_string_to_return_0 = "270f"
    hashed_values = [hash_string_to_return_0, hash_string_to_return_1]

    def hexdigest_side_effect():  # type: ignore[no-untyped-def]
        return hashed_values.pop()

    mock_hash = mock.MagicMock()
    mock_hashlib.md5.return_value = mock_hash

    mock_hash.hexdigest.side_effect = hexdigest_side_effect

    # -- FINISH SETTING UP THE MOCKS --

    # When
    # we get the hashed percentage value for the given object ids
    value = get_hashed_percentage_for_object_ids(object_ids)

    # Then
    # The value is 0 as defined by the mock data
    assert value == 0

    # and the md5 function was called twice
    # (i.e. the get_hashed_percentage_for_object_ids function was also called twice)
    call_list = mock_hashlib.md5.call_args_list
    assert len(call_list) == 2

    # the first call, with a string (in bytes) that contains each object id once
    expected_bytes_1 = ",".join(str(id_) for id_ in object_ids).encode("utf-8")
    assert call_list[0][0][0] == expected_bytes_1

    # the second call, with a string (in bytes) that contains each object id twice
    expected_bytes_2 = ",".join(str(id_) for id_ in object_ids * 2).encode("utf-8")
    assert call_list[1][0][0] == expected_bytes_2
