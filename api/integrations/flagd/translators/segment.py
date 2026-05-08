"""
Translate Flagsmith segments and rule trees into JsonLogic.

Each Flagsmith ``SegmentModel`` becomes one entry in flagd's
``$evaluators`` block, keyed by a slugified segment name. Flag targeting
expressions reference segments via ``{"$ref": "<segment-key>"}``.

Nested ``SegmentRuleModel`` trees are inlined into the segment evaluator
because flagd does not allow nested ``$ref``s.
"""

import re
from typing import Iterable

from integrations.flagd.exceptions import UntranslatableConditionError
from integrations.flagd.translators.operators import condition_to_jsonlogic
from integrations.flagd.types import JsonLogic, TranslationWarning
from util.engine_models.segments.models import SegmentModel, SegmentRuleModel


def segment_to_jsonlogic(
    segment: SegmentModel,
    *,
    feature_key: str | None = None,
    warnings: list[TranslationWarning] | None = None,
) -> JsonLogic | None:
    """
    Convert a segment's rule tree to a single JsonLogic expression that
    returns ``true`` when an identity matches the segment.

    Returns ``None`` if the segment has no rules to evaluate.
    """
    if not segment.rules:
        return None
    return _rules_to_jsonlogic(
        segment.rules,
        rule_type="ALL",
        feature_key=feature_key,
        warnings=warnings,
    )


def rule_to_jsonlogic(
    rule: SegmentRuleModel,
    *,
    feature_key: str | None = None,
    warnings: list[TranslationWarning] | None = None,
) -> JsonLogic | None:
    """
    Translate a single rule node (and its descendants).
    """
    expressions: list[JsonLogic] = []

    for condition in rule.conditions:
        try:
            expressions.append(
                condition_to_jsonlogic(condition, feature_key=feature_key)
            )
        except UntranslatableConditionError as exc:
            if warnings is not None:
                warnings.append(
                    TranslationWarning(
                        reason=exc.reason,
                        detail=f"operator={exc.operator}, property={condition.property_}",
                    )
                )

    for child in rule.rules:
        child_logic = rule_to_jsonlogic(
            child, feature_key=feature_key, warnings=warnings
        )
        if child_logic is not None:
            expressions.append(child_logic)

    if not expressions:
        return None

    return _combine(rule.type, expressions)


def slugify_name(name: str, *, fallback: str = "unnamed") -> str:
    """
    Produce a flagd-safe key from a user-supplied name. Strips
    characters outside ``[A-Za-z0-9_-]`` and collapses runs into single
    hyphens.
    """
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", name.strip()) or fallback
    cleaned = cleaned.strip("-_") or fallback
    return cleaned


def slugify_segment_name(name: str, *, taken: Iterable[str] = ()) -> str:
    """
    Produce a flagd-safe key for a segment. Segment names are
    user-supplied and may collide once normalised, so callers can pass
    in a set of already-used keys to suffix-disambiguate.
    """
    cleaned = slugify_name(name, fallback="segment")
    if cleaned not in taken:
        return cleaned
    counter = 2
    while True:
        candidate = f"{cleaned}-{counter}"
        if candidate not in taken:
            return candidate
        counter += 1


def _rules_to_jsonlogic(
    rules: list[SegmentRuleModel],
    *,
    rule_type: str,
    feature_key: str | None,
    warnings: list[TranslationWarning] | None,
) -> JsonLogic | None:
    expressions: list[JsonLogic] = []
    for rule in rules:
        translated = rule_to_jsonlogic(
            rule, feature_key=feature_key, warnings=warnings
        )
        if translated is not None:
            expressions.append(translated)
    if not expressions:
        return None
    if len(expressions) == 1 and rule_type == "ALL":
        return expressions[0]
    return _combine(rule_type, expressions)


def _combine(rule_type: str, expressions: list[JsonLogic]) -> JsonLogic:
    if rule_type == "ALL":
        return {"and": expressions} if len(expressions) > 1 else expressions[0]
    if rule_type == "ANY":
        return {"or": expressions} if len(expressions) > 1 else expressions[0]
    if rule_type == "NONE":
        inner: JsonLogic = (
            {"or": expressions} if len(expressions) > 1 else expressions[0]
        )
        return {"!": inner}
    # Defensive: unknown rule type — fall back to AND so we don't silently
    # broaden the audience.
    return {"and": expressions}
