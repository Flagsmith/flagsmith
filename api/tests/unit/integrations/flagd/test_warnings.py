"""
Unit tests for warning emission during segment translation.

The segment translator catches ``UntranslatableConditionError`` and records
a ``TranslationWarning`` so callers can surface skipped conditions in the
sync response.
"""

import pytest
from flag_engine.segments import constants as op

from integrations.flagd.constants import (
    WARNING_MALFORMED_VALUE,
    WARNING_REGEX_UNSUPPORTED,
    WARNING_UNKNOWN_OPERATOR,
)
from integrations.flagd.translators.segment import segment_to_jsonlogic
from integrations.flagd.types import TranslationWarning
from util.engine_models.segments.models import (
    SegmentConditionModel,
    SegmentModel,
    SegmentRuleModel,
)


def _wrap(condition: SegmentConditionModel) -> SegmentModel:
    return SegmentModel(
        id=1,
        name="test-segment",
        rules=[SegmentRuleModel(type="ALL", conditions=[condition])],
    )


def test_segment_to_jsonlogic__regex_condition__emits_regex_warning() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.REGEX, property_="email", value=".*@flagsmith.com"
    )
    segment = _wrap(condition)
    warnings: list[TranslationWarning] = []

    # When
    logic = segment_to_jsonlogic(segment, warnings=warnings)

    # Then
    assert logic is None  # the only condition was skipped
    assert warnings == [
        TranslationWarning(
            reason=WARNING_REGEX_UNSUPPORTED,
            detail=f"operator={op.REGEX}, property=email",
        )
    ]


def test_segment_to_jsonlogic__unknown_operator__emits_unknown_operator_warning() -> None:
    # Given -- bypass pydantic validation by constructing then mutating, since
    # ConditionOperator is a constrained enum-like type.
    condition = SegmentConditionModel(
        operator=op.EQUAL, property_="trait", value="x"
    )
    object.__setattr__(condition, "operator", "TOTALLY_UNKNOWN")
    segment = _wrap(condition)
    warnings: list[TranslationWarning] = []

    # When
    logic = segment_to_jsonlogic(segment, warnings=warnings)

    # Then
    assert logic is None
    assert warnings == [
        TranslationWarning(
            reason=WARNING_UNKNOWN_OPERATOR,
            detail="operator=TOTALLY_UNKNOWN, property=trait",
        )
    ]


def test_segment_to_jsonlogic__malformed_modulo_value__emits_malformed_warning() -> None:
    # Given
    condition = SegmentConditionModel(
        operator=op.MODULO, property_="user_id", value="abc"
    )
    segment = _wrap(condition)
    warnings: list[TranslationWarning] = []

    # When
    logic = segment_to_jsonlogic(segment, warnings=warnings)

    # Then
    assert logic is None
    assert warnings == [
        TranslationWarning(
            reason=WARNING_MALFORMED_VALUE,
            detail=f"operator={op.MODULO}, property=user_id",
        )
    ]


def test_segment_to_jsonlogic__semver_suffix_only__emits_malformed_warning() -> None:
    # Given -- value is just the suffix, no version part.
    condition = SegmentConditionModel(
        operator=op.EQUAL, property_="version", value=":semver"
    )
    segment = _wrap(condition)
    warnings: list[TranslationWarning] = []

    # When
    logic = segment_to_jsonlogic(segment, warnings=warnings)

    # Then
    assert logic is None
    assert warnings == [
        TranslationWarning(
            reason=WARNING_MALFORMED_VALUE,
            detail=f"operator={op.EQUAL}, property=version",
        )
    ]


def test_segment_to_jsonlogic__warning_alongside_translatable_condition__keeps_translatable() -> None:
    # Given -- one regex (skipped) plus one valid equality (kept).
    segment = SegmentModel(
        id=2,
        name="mixed",
        rules=[
            SegmentRuleModel(
                type="ALL",
                conditions=[
                    SegmentConditionModel(
                        operator=op.REGEX,
                        property_="email",
                        value=".*",
                    ),
                    SegmentConditionModel(
                        operator=op.EQUAL,
                        property_="plan",
                        value="premium",
                    ),
                ],
            )
        ],
    )
    warnings: list[TranslationWarning] = []

    # When
    logic = segment_to_jsonlogic(segment, warnings=warnings)

    # Then
    assert logic == {"==": [{"var": "plan"}, "premium"]}
    assert len(warnings) == 1
    assert warnings[0]["reason"] == WARNING_REGEX_UNSUPPORTED


def test_segment_to_jsonlogic__no_warnings_list__silently_skips_untranslatable() -> None:
    # Given -- caller passes None for warnings, indicating they don't care.
    condition = SegmentConditionModel(
        operator=op.REGEX, property_="email", value=".*"
    )
    segment = _wrap(condition)

    # When
    logic = segment_to_jsonlogic(segment)  # warnings defaults to None

    # Then -- must not raise; condition silently dropped.
    assert logic is None


@pytest.mark.parametrize(
    "raw_value,operator,reason",
    [
        ("not-a-number", op.GREATER_THAN, WARNING_MALFORMED_VALUE),
        ("not-a-number", op.LESS_THAN_INCLUSIVE, WARNING_MALFORMED_VALUE),
        ("oops", op.PERCENTAGE_SPLIT, WARNING_MALFORMED_VALUE),
    ],
)
def test_segment_to_jsonlogic__malformed_numeric_value__emits_malformed_warning(
    raw_value: str, operator: str, reason: str
) -> None:
    # Given
    condition = SegmentConditionModel(
        operator=operator, property_="trait", value=raw_value
    )
    segment = _wrap(condition)
    warnings: list[TranslationWarning] = []

    # When
    logic = segment_to_jsonlogic(segment, warnings=warnings)

    # Then
    assert logic is None
    assert warnings == [
        TranslationWarning(
            reason=reason,
            detail=f"operator={operator}, property=trait",
        )
    ]
