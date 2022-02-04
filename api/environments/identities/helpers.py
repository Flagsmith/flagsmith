import hashlib
import typing


def get_hashed_percentage_for_object_ids(
    object_ids: typing.Iterable[int], iterations: int = 1
) -> float:
    """
    Given a list of object ids, get a floating point number between 0 and 1 based on
    the hash of those ids. This should give the same value every time for any
    list of ids.

    :param object_ids: list of object ids to calculate the has for
    :param iterations: num times to include each id in the generated string to hash
    :return: (float) number between 0 (inclusive) and 1 (exclusive)
    """

    to_hash = ",".join(str(id_) for id_ in list(object_ids) * iterations)
    hashed_value = hashlib.md5(to_hash.encode("utf-8"))
    hashed_value_as_int = int(hashed_value.hexdigest(), base=16)
    value = (hashed_value_as_int % 9999) / 9998

    if value == 1:
        # since we want a number between 0 (inclusive) and 1 (exclusive), in the
        # unlikely case that we get the exact number 1, we call the method again
        # and increase the number of iterations to ensure we get a different result
        return get_hashed_percentage_for_object_ids(
            object_ids=object_ids, iterations=iterations + 1
        )

    return value
