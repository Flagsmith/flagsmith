"""
Unit tests for ``integrations.flagd.translators.segment``.

These tests exercise rule-tree translation -- combination of ``ALL``/``ANY``/
``NONE`` rules, deep nesting, mixed operators, empty rules, and the
``slugify_segment_name`` helper.
"""

import pytest
from flag_engine.segments import constants as op

from integrations.flagd.translators.segment import (
    rule_to_jsonlogic,
    segment_to_jsonlogic,
    slugify_segment_name,
)
from util.engine_models.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)


# ---------------------------------------------------------------------------
# Single-rule ALL / ANY / NONE
# ---------------------------------------------------------------------------


def _eq(prop: str, value: str) -> SegmentConditionModel:
    return SegmentConditionModel(operator=op.EQUAL, property_=prop, value=value)


def test_segment_to_jsonlogic__single_all_rule__returns_combined_and() -> None:
    # Given
    segment = SegmentModel(
        id=1,
        name="all-segment",
        rules=[
            SegmentRuleModel(
                type="ALL",
                conditions=[_eq("a", "1"), _eq("b", "2")],
            )
        ],
    )

    # When
    logic = segment_to_jsonlogic(segment)

    # Then
    assert logic == {
        "and": [
            {"==": [{"var": "a"}, 1]},
            {"==": [{"var": "b"}, 2]},
        ]
    }


def test_segment_to_jsonlogic__single_any_rule__returns_or() -> None:
    # Given
    segment = SegmentModel(
        id=2,
        name="any-segment",
        rules=[
            SegmentRuleModel(
                type="ANY",
                conditions=[_eq("a", "1"), _eq("b", "2")],
            )
        ],
    )

    # When
    logic = segment_to_jsonlogic(segment)

    # Then
    assert logic == {
        "or": [
            {"==": [{"var": "a"}, 1]},
            {"==": [{"var": "b"}, 2]},
        ]
    }


def test_segment_to_jsonlogic__single_none_rule__returns_negated_or() -> None:
    # Given
    segment = SegmentModel(
        id=3,
        name="none-segment",
        rules=[
            SegmentRuleModel(
                type="NONE",
                conditions=[_eq("a", "1"), _eq("b", "2")],
            )
        ],
    )

    # When
    logic = segment_to_jsonlogic(segment)

    # Then
    assert logic == {
        "!": {
            "or": [
                {"==": [{"var": "a"}, 1]},
                {"==": [{"var": "b"}, 2]},
            ]
        }
    }


def test_segment_to_jsonlogic__single_condition__omits_redundant_combinator() -> None:
    # Given
    segment = SegmentModel(
        id=4,
        name="lone",
        rules=[
            SegmentRuleModel(
                type="ALL",
                conditions=[_eq("a", "1")],
            )
        ],
    )

    # When
    logic = segment_to_jsonlogic(segment)

    # Then -- a single condition does not need to be wrapped in `and`.
    assert logic == {"==": [{"var": "a"}, 1]}


# ---------------------------------------------------------------------------
# Three-level nesting: NONE > ANY > ALL
# ---------------------------------------------------------------------------


def test_segment_to_jsonlogic__three_level_nested_rules__produces_deep_tree() -> None:
    # Given
    inner_all = SegmentRuleModel(
        type="ALL",
        conditions=[_eq("country", "GB"), _eq("plan", "premium")],
    )
    middle_any = SegmentRuleModel(
        type="ANY",
        conditions=[_eq("beta", "true")],
        rules=[inner_all],
    )
    outer_none = SegmentRuleModel(
        type="NONE",
        rules=[middle_any],
    )
    segment = SegmentModel(id=5, name="deep", rules=[outer_none])

    # When
    logic = segment_to_jsonlogic(segment)

    # Then
    assert logic == {
        "!": {
            "or": [
                {"==": [{"var": "beta"}, True]},
                {
                    "and": [
                        {"==": [{"var": "country"}, "GB"]},
                        {"==": [{"var": "plan"}, "premium"]},
                    ]
                },
            ]
        }
    }


# ---------------------------------------------------------------------------
# Mixed operators
# ---------------------------------------------------------------------------


def test_segment_to_jsonlogic__mixed_operators__translates_each() -> None:
    # Given
    segment = SegmentModel(
        id=6,
        name="mixed",
        rules=[
            SegmentRuleModel(
                type="ALL",
                conditions=[
                    SegmentConditionModel(
                        operator=op.GREATER_THAN, property_="age", value="18"
                    ),
                    SegmentConditionModel(
                        operator=op.CONTAINS,
                        property_="email",
                        value="@flagsmith.com",
                    ),
                    SegmentConditionModel(
                        operator=op.IN,
                        property_="country",
                        value="GB,US",
                    ),
                ],
            )
        ],
    )

    # When
    logic = segment_to_jsonlogic(segment)

    # Then
    assert logic == {
        "and": [
            {">": [{"var": "age"}, 18]},
            {"in": ["@flagsmith.com", {"var": "email"}]},
            {"in": [{"var": "country"}, ["GB", "US"]]},
        ]
    }


# ---------------------------------------------------------------------------
# Empty rule / segment
# ---------------------------------------------------------------------------


def test_segment_to_jsonlogic__no_rules__returns_none() -> None:
    # Given
    segment = SegmentModel(id=7, name="empty", rules=[])

    # When
    logic = segment_to_jsonlogic(segment)

    # Then
    assert logic is None


def test_rule_to_jsonlogic__rule_without_conditions_or_children__returns_none() -> None:
    # Given
    rule = SegmentRuleModel(type="ALL")

    # When
    logic = rule_to_jsonlogic(rule)

    # Then
    assert logic is None


def test_segment_to_jsonlogic__rule_with_only_empty_children__returns_none() -> None:
    # Given
    segment = SegmentModel(
        id=8,
        name="hollow",
        rules=[
            SegmentRuleModel(
                type="ANY",
                rules=[SegmentRuleModel(type="ALL")],
            )
        ],
    )

    # When
    logic = segment_to_jsonlogic(segment)

    # Then
    assert logic is None


# ---------------------------------------------------------------------------
# PERCENTAGE_SPLIT inside a rule
# ---------------------------------------------------------------------------


def test_segment_to_jsonlogic__percentage_split_condition__translates_with_feature_key() -> None:
    # Given
    segment = SegmentModel(
        id=9,
        name="rollout",
        rules=[
            SegmentRuleModel(
                type="ALL",
                conditions=[
                    SegmentConditionModel(
                        operator=op.PERCENTAGE_SPLIT, value="42"
                    )
                ],
            )
        ],
    )

    # When
    logic = segment_to_jsonlogic(segment, feature_key="dark-launch")

    # Then
    assert logic == {
        "==": [
            {
                "fractional": [
                    {"cat": [{"var": "targetingKey"}, "dark-launch"]},
                    ["in", 42.0],
                    ["out", 58.0],
                ]
            },
            "in",
        ]
    }


# ---------------------------------------------------------------------------
# slugify_segment_name
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,expected",
    [
        ("My Segment", "My-Segment"),
        ("  spaced out  ", "spaced-out"),
        ("safe-name_1", "safe-name_1"),
        ("!!!", "segment"),
        ("---weird---", "weird"),
        ("emoji rocket", "emoji-rocket"),
    ],
)
def test_slugify_segment_name__various_inputs__produces_safe_key(
    name: str, expected: str
) -> None:
    # Given / When
    result = slugify_segment_name(name)

    # Then
    assert result == expected


def test_slugify_segment_name__case_preserved__no_collision_with_lowercase() -> None:
    # Given -- slugifier is case-preserving, so "My Segment" -> "My-Segment".
    taken = {"my-segment"}

    # When
    result = slugify_segment_name("My Segment", taken=taken)

    # Then
    assert result == "My-Segment"


def test_slugify_segment_name__direct_collision__increments_counter() -> None:
    # Given
    taken = {"my-segment"}

    # When
    result = slugify_segment_name("my-segment", taken=taken)

    # Then
    assert result == "my-segment-2"


def test_slugify_segment_name__multiple_collisions__keeps_incrementing() -> None:
    # Given
    taken = {"my-segment", "my-segment-2", "my-segment-3"}

    # When
    result = slugify_segment_name("my-segment", taken=taken)

    # Then
    assert result == "my-segment-4"
