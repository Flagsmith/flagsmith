import pytest
from core.constants import STRING

from features.utils import MAX_INTEGER_SIZE, MIN_INTEGER_SIZE, get_value_type


@pytest.mark.parametrize("value", (MIN_INTEGER_SIZE - 1, MAX_INTEGER_SIZE + 1))
def test_get_value_type_returns_string_for_integer_out_of_bounds(value):
    assert get_value_type(value) == STRING
