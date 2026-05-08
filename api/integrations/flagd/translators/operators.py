"""
Translate a single Flagsmith ``SegmentConditionModel`` into a JsonLogic
expression understood by flagd.

The translator is a pure function over the engine model so that callers
work against the same data shape that the SDK environment-document
endpoint already produces.
"""

from typing import Any

from flag_engine.segments import constants as op

from integrations.flagd.constants import (
    WARNING_MALFORMED_VALUE,
    WARNING_REGEX_UNSUPPORTED,
    WARNING_UNKNOWN_OPERATOR,
)
from integrations.flagd.exceptions import UntranslatableConditionError
from integrations.flagd.types import JsonLogic
from util.engine_models.segments.models import SegmentConditionModel

_SEMVER_SUFFIX = ":semver"
_SEMVER_OPERATOR_MAP = {
    op.EQUAL: "=",
    op.NOT_EQUAL: "!=",
    op.GREATER_THAN: ">",
    op.GREATER_THAN_INCLUSIVE: ">=",
    op.LESS_THAN: "<",
    op.LESS_THAN_INCLUSIVE: "<=",
}


def condition_to_jsonlogic(
    condition: SegmentConditionModel,
    *,
    feature_key: str | None = None,
) -> JsonLogic:
    """
    Convert a Flagsmith condition to JsonLogic.

    Raises ``UntranslatableConditionError`` when the operator has no
    flagd equivalent (e.g. REGEX) or the value is malformed; callers are
    expected to skip such conditions and emit a warning.
    """
    operator = condition.operator
    raw_value = condition.value
    property_name = condition.property_

    if operator == op.IS_SET:
        return {"!=": [_var(property_name), None]}
    if operator == op.IS_NOT_SET:
        return {"==": [_var(property_name), None]}

    if operator == op.REGEX:
        raise UntranslatableConditionError(
            WARNING_REGEX_UNSUPPORTED, operator=operator
        )

    if raw_value is None:
        raise UntranslatableConditionError(
            WARNING_MALFORMED_VALUE, operator=operator
        )

    if _is_semver_value(raw_value):
        return _semver_jsonlogic(property_name, operator, raw_value)

    if operator in (op.EQUAL, op.NOT_EQUAL):
        jsonlogic_op = "==" if operator == op.EQUAL else "!="
        return {jsonlogic_op: [_var(property_name), _coerce_value(raw_value)]}

    if operator in (
        op.GREATER_THAN,
        op.GREATER_THAN_INCLUSIVE,
        op.LESS_THAN,
        op.LESS_THAN_INCLUSIVE,
    ):
        jsonlogic_op = {
            op.GREATER_THAN: ">",
            op.GREATER_THAN_INCLUSIVE: ">=",
            op.LESS_THAN: "<",
            op.LESS_THAN_INCLUSIVE: "<=",
        }[operator]
        try:
            numeric_value: Any = float(raw_value)
            if numeric_value.is_integer():
                numeric_value = int(numeric_value)
        except (TypeError, ValueError) as exc:
            raise UntranslatableConditionError(
                WARNING_MALFORMED_VALUE, operator=operator
            ) from exc
        return {jsonlogic_op: [_var(property_name), numeric_value]}

    if operator == op.CONTAINS:
        return {"in": [raw_value, _var(property_name)]}
    if operator == op.NOT_CONTAINS:
        return {"!": {"in": [raw_value, _var(property_name)]}}

    if operator == op.IN:
        members = [v for v in (m.strip() for m in raw_value.split(",")) if v]
        return {"in": [_var(property_name), members]}

    if operator == op.MODULO:
        try:
            divisor_str, remainder_str = raw_value.split("|", 1)
            divisor: float = float(divisor_str)
            remainder: float = float(remainder_str)
        except ValueError as exc:
            raise UntranslatableConditionError(
                WARNING_MALFORMED_VALUE, operator=operator
            ) from exc
        return {"==": [{"%": [_var(property_name), divisor]}, remainder]}

    if operator == op.PERCENTAGE_SPLIT:
        try:
            threshold = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise UntranslatableConditionError(
                WARNING_MALFORMED_VALUE, operator=operator
            ) from exc
        # PERCENTAGE_SPLIT in Flagsmith means "this identity falls under X%".
        # Express as a fractional bucket: targetingKey lands in the "in"
        # bucket of size `threshold` or the "out" bucket of size 100 - threshold.
        bucket_seed_parts: list[Any] = [{"var": "targetingKey"}]
        if feature_key:
            bucket_seed_parts.append(feature_key)
        return {
            "==": [
                {
                    "fractional": [
                        {"cat": bucket_seed_parts}
                        if feature_key
                        else {"var": "targetingKey"},
                        ["in", threshold],
                        ["out", max(0.0, 100.0 - threshold)],
                    ]
                },
                "in",
            ]
        }

    raise UntranslatableConditionError(
        WARNING_UNKNOWN_OPERATOR, operator=operator
    )


def _var(property_name: str | None) -> JsonLogic:
    return {"var": property_name or ""}


def _coerce_value(raw: str) -> Any:
    """Best-effort native typing for equality comparisons."""
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw == "null":
        return None
    try:
        as_int = int(raw)
        # Avoid losing leading zeros for things like "007".
        if str(as_int) == raw:
            return as_int
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _is_semver_value(raw: str) -> bool:
    return isinstance(raw, str) and raw.endswith(_SEMVER_SUFFIX)


def _semver_jsonlogic(
    property_name: str | None,
    operator: str,
    raw_value: str,
) -> JsonLogic:
    if operator not in _SEMVER_OPERATOR_MAP:
        raise UntranslatableConditionError(
            WARNING_MALFORMED_VALUE, operator=operator
        )
    version = raw_value[: -len(_SEMVER_SUFFIX)].strip()
    if not version:
        raise UntranslatableConditionError(
            WARNING_MALFORMED_VALUE, operator=operator
        )
    return {
        "sem_ver": [
            _var(property_name),
            _SEMVER_OPERATOR_MAP[operator],
            version,
        ]
    }
