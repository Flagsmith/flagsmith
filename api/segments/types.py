from flag_engine.segments.types import ConditionOperator, RuleType
from typing_extensions import NotRequired, TypedDict


class SegmentEngineMetadata(TypedDict):
    pk: int


class SegmentCondition(TypedDict):
    property: str | None
    operator: ConditionOperator
    value: str | None
    description: str | None


class _BaseSegmentRule(TypedDict):
    type: RuleType
    conditions: list[SegmentCondition]


class _NestedSegmentRule(_BaseSegmentRule):
    pass


class SegmentRule(_BaseSegmentRule):
    rules: list[_NestedSegmentRule]


class LegacySegmentCondition(SegmentCondition):
    id: NotRequired[int]
    delete: NotRequired[bool]


class _BaseLegacySegmentRule(TypedDict):
    id: NotRequired[int]
    delete: NotRequired[bool]
    type: RuleType
    conditions: list[LegacySegmentCondition]


class LegacyNestedSegmentRule(_BaseLegacySegmentRule):
    pass


class LegacySegmentRule(_BaseLegacySegmentRule):
    rules: list[LegacyNestedSegmentRule]
