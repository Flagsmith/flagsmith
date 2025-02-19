import pytest

from custom_auth.oauth.exceptions import GithubError
from custom_auth.oauth.helpers.github_helpers import (
    convert_response_data_to_dictionary,
    get_first_and_last_name,
)


def test_convert_response_data_to_dictionary_success():  # type: ignore[no-untyped-def]
    # Given
    response_string = "key_1=value_1&key_2=value_2&key_3=value_3"

    # When
    response_dict = convert_response_data_to_dictionary(response_string)

    # Then
    assert response_dict == {
        "key_1": "value_1",
        "key_2": "value_2",
        "key_3": "value_3",
    }


def test_convert_response_data_to_dictionary_fail():  # type: ignore[no-untyped-def]
    # Given
    response_string = "key_1value_1&key_2=value_2=value_2"

    # When
    with pytest.raises(GithubError):
        convert_response_data_to_dictionary(response_string)

    # Then - exception raised


def test_get_first_and_last_name_success():  # type: ignore[no-untyped-def]
    # Given
    full_name = "tommy tester"

    # When
    first_name, last_name = get_first_and_last_name(full_name)

    # Then
    assert first_name == "tommy"
    assert last_name == "tester"


def test_get_first_and_last_name_too_many_names():  # type: ignore[no-untyped-def]
    # Given
    full_name = "tommy tester the third king among testers"

    # When
    first_name, last_name = get_first_and_last_name(full_name)

    # Then
    assert first_name == full_name
    assert last_name == ""


def test_get_first_and_last_name_too_few_names():  # type: ignore[no-untyped-def]
    # Given
    full_name = "wall-e"

    # When
    first_name, last_name = get_first_and_last_name(full_name)

    # Then
    assert first_name == full_name
    assert last_name == ""
