from flag_engine.segments.types import ConditionOperator, RuleType
from typing_extensions import NotRequired, TypedDict


class SegmentEngineMetadata(TypedDict):
    pk: int


class SegmentCondition(TypedDict):
    property: str | None
    operator: ConditionOperator
    value: str | None
    description: str | None


class SegmentRule(TypedDict):
    type: RuleType
    conditions: list[SegmentCondition]
    rules: list["SegmentRule"]


class LegacySegmentCondition(SegmentCondition):
    id: NotRequired[int]
    delete: NotRequired[bool]


class LegacySegmentRule(TypedDict):
    id: NotRequired[int]
    delete: NotRequired[bool]
    type: RuleType
    conditions: list[LegacySegmentCondition]
    rules: list["LegacySegmentRule"]
