"""
Hypothesis-driven smoke tests that assert the translation pipeline
never crashes and produces output a JsonLogic evaluator can parse.

These complement the targeted parametrised tests with broad coverage of
arbitrary segment trees and value shapes.
"""

from __future__ import annotations

import pytest
from flag_engine.segments import constants as op
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from integrations.flagd.translators.operators import condition_to_jsonlogic
from integrations.flagd.translators.segment import (
    rule_to_jsonlogic,
    segment_to_jsonlogic,
    slugify_segment_name,
)
from integrations.flagd.types import TranslationWarning
from util.engine_models.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)

# Operators safe to feed arbitrary string values to without raising.
_SAFE_STRING_OPERATORS = [
    op.EQUAL,
    op.NOT_EQUAL,
    op.CONTAINS,
    op.NOT_CONTAINS,
    op.IN,
    op.IS_SET,
    op.IS_NOT_SET,
]


@st.composite
def conditions(draw: st.DrawFn) -> SegmentConditionModel:
    operator = draw(st.sampled_from(_SAFE_STRING_OPERATORS))
    property_name = draw(
        st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=20)
    )
    if operator in (op.IS_SET, op.IS_NOT_SET):
        value = None
    else:
        value = draw(st.text(min_size=0, max_size=30))
    return SegmentConditionModel(
        operator=operator, property_=property_name, value=value
    )


@st.composite
def rules(draw: st.DrawFn, depth: int = 2) -> SegmentRuleModel:
    rule_type = draw(st.sampled_from(["ALL", "ANY", "NONE"]))
    cond_list = draw(st.lists(conditions(), min_size=0, max_size=3))
    sub_rules: list[SegmentRuleModel] = []
    if depth > 0:
        sub_rules = draw(st.lists(rules(depth - 1), min_size=0, max_size=2))
    return SegmentRuleModel(type=rule_type, conditions=cond_list, rules=sub_rules)


@given(condition=conditions())
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_condition_to_jsonlogic__arbitrary_supported_operator__never_crashes(
    condition: SegmentConditionModel,
) -> None:
    # Given any supported operator with a random value
    # When the translator runs
    result = condition_to_jsonlogic(condition)
    # Then it returns a non-empty dict
    assert isinstance(result, dict)
    assert result


@given(rule=rules())
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_rule_to_jsonlogic__arbitrary_tree__returns_dict_or_none(
    rule: SegmentRuleModel,
) -> None:
    # Given any rule tree of conditions
    warnings: list[TranslationWarning] = []
    # When the rule is translated
    result = rule_to_jsonlogic(rule, warnings=warnings)
    # Then the result is None (when no clauses) or a dict
    assert result is None or isinstance(result, dict)


@given(
    name=st.text(
        alphabet=st.characters(blacklist_categories=("Cs",)),
        min_size=1,
        max_size=20,
    ),
)
@settings(max_examples=30)
def test_slugify_segment_name__arbitrary_input__produces_safe_key(
    name: str,
) -> None:
    # Given any user-supplied segment name
    # When the slug is computed
    slug = slugify_segment_name(name)
    # Then it only contains characters flagd accepts in $evaluator keys
    assert slug
    assert all(ch.isalnum() or ch in "-_" for ch in slug)


@given(rules_=st.lists(rules(), min_size=0, max_size=3))
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
def test_segment_to_jsonlogic__arbitrary_segment__valid_or_none(
    rules_: list[SegmentRuleModel],
) -> None:
    # Given a randomly generated segment
    segment = SegmentModel(id=1, name="random", rules=rules_)
    # When translated
    warnings: list[TranslationWarning] = []
    result = segment_to_jsonlogic(segment, warnings=warnings)
    # Then the result is None or a dict
    assert result is None or isinstance(result, dict)


@pytest.mark.parametrize(
    "name,expected_prefix",
    [
        ("My Segment!", "My-Segment"),
        ("   ", "segment"),
        ("---", "segment"),
        ("naïve customers ✨", "na-ve-customers"),
    ],
)
def test_slugify_segment_name__various_inputs__match_expected_prefix(
    name: str, expected_prefix: str
) -> None:
    # Given a segment name
    # When slugified
    slug = slugify_segment_name(name)
    # Then it starts with the expected normalised form
    assert slug.startswith(expected_prefix)
