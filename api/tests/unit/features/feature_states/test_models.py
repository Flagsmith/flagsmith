import pytest

from features.models import FeatureState
from features.value_types import BOOLEAN, INTEGER, STRING


@pytest.mark.parametrize(
    "value,type_,expected_value,expected_type",
    [
        ("hello", "string", "hello", STRING),
        ("42", "integer", 42, INTEGER),
        ("true", "boolean", True, BOOLEAN),
        ("false", "boolean", False, BOOLEAN),
        ("TRUE", "boolean", True, BOOLEAN),
    ],
)
def test_set_value(
    feature_state: FeatureState,
    value: str,
    type_: str,
    expected_value: str | int | bool,
    expected_type: str,
) -> None:
    # Given
    fsv = feature_state.feature_state_value

    # When
    fsv.set_value(value, type_)

    # Then
    assert fsv.value == expected_value
    assert fsv.type == expected_type


@pytest.mark.parametrize(
    "value,type_,expected_error",
    [
        ("not_a_number", "integer", "'not_a_number' is not a valid integer"),
        ("yes", "boolean", "'yes' is not a valid boolean"),
        ("hello", "invalid", "'invalid' is not a valid type"),
    ],
)
def test_set_value_invalid_raises_error(
    feature_state: FeatureState,
    value: str,
    type_: str,
    expected_error: str,
) -> None:
    # Given
    fsv = feature_state.feature_state_value

    # When / Then
    with pytest.raises(ValueError) as exc_info:
        fsv.set_value(value, type_)

    assert expected_error in str(exc_info.value)


def test_set_value_clears_old_fields_when_changing_type(
    feature_state: FeatureState,
) -> None:
    # Given
    fsv = feature_state.feature_state_value
    fsv.set_value("42", "integer")
    fsv.save()

    assert fsv.integer_value == 42

    # When - change from integer to string
    fsv.set_value("hello", "string")

    # Then - integer_value should be cleared
    assert fsv.string_value == "hello"
    assert fsv.integer_value is None
    assert fsv.boolean_value is None
    assert fsv.type == STRING


@pytest.mark.parametrize(
    "invalid_value,invalid_type",
    [
        ("not_a_number", "integer"),
        ("yes", "boolean"),
        ("hello", "invalid_type"),
    ],
)
def test_set_value_preserves_original_value_on_error(
    feature_state: FeatureState,
    invalid_value: str,
    invalid_type: str,
) -> None:
    # Given
    fsv = feature_state.feature_state_value
    fsv.set_value("42", "integer")
    fsv.save()

    assert fsv.integer_value == 42
    assert fsv.type == INTEGER

    # When - try to set invalid value
    with pytest.raises(ValueError):
        fsv.set_value(invalid_value, invalid_type)

    # Then - original value should be preserved
    assert fsv.integer_value == 42
    assert fsv.type == INTEGER
    assert fsv.value == 42
