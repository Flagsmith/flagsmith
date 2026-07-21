import pytest

from custom_auth.oauth.exceptions import GithubError
from custom_auth.oauth.helpers.github_helpers import (
    convert_response_data_to_dictionary,
    get_first_and_last_name,
)


def test_convert_response_data_to_dictionary__valid_string__returns_dict():  # type: ignore[no-untyped-def]
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


def test_convert_response_data_to_dictionary__invalid_string__raises_github_error():  # type: ignore[no-untyped-def]
    # Given
    response_string = "key_1value_1&key_2=value_2=value_2"

    # When / Then
    with pytest.raises(GithubError):
        convert_response_data_to_dictionary(response_string)


def test_get_first_and_last_name__two_part_name__returns_first_and_last():  # type: ignore[no-untyped-def]
    # Given
    full_name = "tommy tester"

    # When
    first_name, last_name = get_first_and_last_name(full_name)

    # Then
    assert first_name == "tommy"
    assert last_name == "tester"


def test_get_first_and_last_name__too_many_names__returns_full_name_as_first():  # type: ignore[no-untyped-def]
    # Given
    full_name = "tommy tester the third king among testers"

    # When
    first_name, last_name = get_first_and_last_name(full_name)

    # Then
    assert first_name == full_name
    assert last_name == ""


def test_get_first_and_last_name__single_name__returns_full_name_as_first():  # type: ignore[no-untyped-def]
    # Given
    full_name = "wall-e"

    # When
    first_name, last_name = get_first_and_last_name(full_name)

    # Then
    assert first_name == full_name
    assert last_name == ""
