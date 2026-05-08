"""
Unit tests for ``integrations.flagd.translators.operators.condition_to_jsonlogic``.

Each operator is exercised with:

* a golden assertion comparing the produced JsonLogic to its expected dict;
* (where meaningful) a runtime evaluation via ``json_logic.jsonLogic`` to
  verify the produced expression has the intended semantics.

Operators backed by flagd-specific extensions (``sem_ver``, ``fractional``)
or relying on float modulo arithmetic are validated by structural assertions
only -- the stock ``json_logic`` reference implementation does not implement
those operators.
"""

from typing import Any

import pytest
from flag_engine.segments import constants as op
from json_logic import jsonLogic

from integrations.flagd.constants import WARNING_REGEX_UNSUPPORTED
from integrations.flagd.exceptions import UntranslatableConditionError
from integrations.flagd.translators.operators import condition_to_jsonlogic
from util.engine_models.segments.models import SegmentConditionModel


# ---------------------------------------------------------------------------
# EQUAL / NOT_EQUAL
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_value,coerced",
    [
        ("hello", "hello"),
        ("true", True),
        ("false", False),
        ("null", None),
        ("42", 42),
        ("3.14", 3.14),
        ("007", 7.0),  # int round-trip mismatch falls through to float
    ],
)
def test_condition_to_jsonlogic__equal__produces_eq_with_coerced_value(
    raw_value: str, coerced: Any
) -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.EQUAL, property_="trait", value=raw_value
    )

    # When
    result = condition_to_jsonlogic(condition)

    # Then
    assert result == {"==": [{"var": "trait"}, coerced]}


def test_condition_to_jsonlogic__equal__matches_at_runtime() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.EQUAL, property_="email", value="x@y.z"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert jsonLogic(logic, {"email": "x@y.z"}) is True
    assert jsonLogic(logic, {"email": "other"}) is False
    assert jsonLogic(logic, {}) is False  # null property


def test_condition_to_jsonlogic__not_equal__matches_at_runtime() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.NOT_EQUAL, property_="email", value="x@y.z"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {"!=": [{"var": "email"}, "x@y.z"]}
    assert jsonLogic(logic, {"email": "other"}) is True
    assert jsonLogic(logic, {"email": "x@y.z"}) is False


# ---------------------------------------------------------------------------
# Numeric comparators
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "operator,jsonlogic_op,raw,expected_value",
    [
        (op.GREATER_THAN, ">", "10", 10),
        (op.GREATER_THAN_INCLUSIVE, ">=", "10.5", 10.5),
        (op.LESS_THAN, "<", "0", 0),
        (op.LESS_THAN_INCLUSIVE, "<=", "-3", -3),
    ],
)
def test_condition_to_jsonlogic__numeric_comparator__produces_expected_logic(
    operator: str,
    jsonlogic_op: str,
    raw: str,
    expected_value: Any,
) -> None:
    # Given
    condition = SegmentConditionModel(
        operator=operator, property_="age", value=raw
    )

    # When
    result = condition_to_jsonlogic(condition)

    # Then
    assert result == {jsonlogic_op: [{"var": "age"}, expected_value]}


def test_condition_to_jsonlogic__greater_than__matches_at_runtime() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.GREATER_THAN, property_="age", value="18"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert jsonLogic(logic, {"age": 21}) is True
    assert jsonLogic(logic, {"age": 18}) is False
    assert jsonLogic(logic, {"age": 5}) is False


def test_condition_to_jsonlogic__less_than_inclusive__matches_at_runtime() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.LESS_THAN_INCLUSIVE, property_="score", value="100"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert jsonLogic(logic, {"score": 100}) is True
    assert jsonLogic(logic, {"score": 99}) is True
    assert jsonLogic(logic, {"score": 101}) is False


# ---------------------------------------------------------------------------
# CONTAINS / NOT_CONTAINS
# ---------------------------------------------------------------------------


def test_condition_to_jsonlogic__contains__produces_in_logic() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.CONTAINS, property_="email", value="@flagsmith.com"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {"in": ["@flagsmith.com", {"var": "email"}]}
    assert jsonLogic(logic, {"email": "ben@flagsmith.com"}) is True
    assert jsonLogic(logic, {"email": "ben@example.com"}) is False


def test_condition_to_jsonlogic__not_contains__produces_negated_in() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.NOT_CONTAINS, property_="email", value="spam"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {"!": {"in": ["spam", {"var": "email"}]}}
    assert jsonLogic(logic, {"email": "good@flagsmith.com"}) is True
    assert jsonLogic(logic, {"email": "spam@bad.com"}) is False


# ---------------------------------------------------------------------------
# IN
# ---------------------------------------------------------------------------


def test_condition_to_jsonlogic__in__produces_membership_logic() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.IN, property_="country", value="GB, US ,DE"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {"in": [{"var": "country"}, ["GB", "US", "DE"]]}
    assert jsonLogic(logic, {"country": "GB"}) is True
    assert jsonLogic(logic, {"country": "FR"}) is False


def test_condition_to_jsonlogic__in__strips_empty_members() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.IN, property_="country", value="GB,,US,"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {"in": [{"var": "country"}, ["GB", "US"]]}


# ---------------------------------------------------------------------------
# IS_SET / IS_NOT_SET
# ---------------------------------------------------------------------------


def test_condition_to_jsonlogic__is_set__produces_not_null_check() -> None:
    # Given
    condition = SegmentConditionModel(operator=op.IS_SET, property_="trait")

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {"!=": [{"var": "trait"}, None]}
    assert jsonLogic(logic, {"trait": "value"}) is True
    assert jsonLogic(logic, {"trait": ""}) is True
    assert jsonLogic(logic, {}) is False


def test_condition_to_jsonlogic__is_not_set__produces_null_check() -> None:
    # Given
    condition = SegmentConditionModel(operator=op.IS_NOT_SET, property_="trait")

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {"==": [{"var": "trait"}, None]}
    assert jsonLogic(logic, {}) is True
    assert jsonLogic(logic, {"trait": "value"}) is False


# ---------------------------------------------------------------------------
# REGEX (always raises)
# ---------------------------------------------------------------------------


def test_condition_to_jsonlogic__regex__raises_untranslatable() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.REGEX, property_="email", value=".*@flagsmith.com"
    )

    # When / Then
    with pytest.raises(UntranslatableConditionError) as exc_info:
        condition_to_jsonlogic(condition)
    assert exc_info.value.reason == WARNING_REGEX_UNSUPPORTED
    assert exc_info.value.operator == op.REGEX


# ---------------------------------------------------------------------------
# MODULO
# ---------------------------------------------------------------------------


def test_condition_to_jsonlogic__modulo__produces_modulo_equality() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.MODULO, property_="user_id", value="3|0"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {
        "==": [{"%": [{"var": "user_id"}, 3.0]}, 0.0]
    }


# ---------------------------------------------------------------------------
# PERCENTAGE_SPLIT
# ---------------------------------------------------------------------------


def test_condition_to_jsonlogic__percentage_split__without_feature_key() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.PERCENTAGE_SPLIT, value="25"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {
        "==": [
            {
                "fractional": [
                    {"var": "targetingKey"},
                    ["in", 25.0],
                    ["out", 75.0],
                ]
            },
            "in",
        ]
    }


def test_condition_to_jsonlogic__percentage_split__with_feature_key() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.PERCENTAGE_SPLIT, value="10"
    )

    # When
    logic = condition_to_jsonlogic(condition, feature_key="my-feature")

    # Then
    assert logic == {
        "==": [
            {
                "fractional": [
                    {"cat": [{"var": "targetingKey"}, "my-feature"]},
                    ["in", 10.0],
                    ["out", 90.0],
                ]
            },
            "in",
        ]
    }


def test_condition_to_jsonlogic__percentage_split__threshold_above_100_clamps_out_bucket() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.PERCENTAGE_SPLIT, value="150"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then -- 100 - 150 would be -50; the translator clamps to 0.0.
    assert logic["=="][0]["fractional"][2] == ["out", 0.0]


# ---------------------------------------------------------------------------
# Sem_Ver suffix handling
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "operator,semver_op",
    [
        (op.EQUAL, "="),
        (op.NOT_EQUAL, "!="),
        (op.GREATER_THAN, ">"),
        (op.GREATER_THAN_INCLUSIVE, ">="),
        (op.LESS_THAN, "<"),
        (op.LESS_THAN_INCLUSIVE, "<="),
    ],
)
def test_condition_to_jsonlogic__semver_suffix__produces_sem_ver_logic(
    operator: str, semver_op: str
) -> None:
    # Given
    condition = SegmentConditionModel(
        operator=operator, property_="version", value="1.2.3:semver"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {"sem_ver": [{"var": "version"}, semver_op, "1.2.3"]}


# ---------------------------------------------------------------------------
# Null property variable shape
# ---------------------------------------------------------------------------


def test_condition_to_jsonlogic__null_property__emits_empty_var_path() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.EQUAL, property_=None, value="anything"
    )

    # When
    logic = condition_to_jsonlogic(condition)

    # Then
    assert logic == {"==": [{"var": ""}, "anything"]}
