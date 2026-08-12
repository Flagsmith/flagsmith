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
    # TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
    id: NotRequired[int]
    delete: NotRequired[bool]


class _BaseLegacySegmentRule(TypedDict):
    # TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
    id: NotRequired[int]
    delete: NotRequired[bool]
    type: RuleType
    conditions: list[LegacySegmentCondition]


class _LegacyNestedSegmentRule(_BaseLegacySegmentRule):
    pass


class LegacySegmentRule(_BaseLegacySegmentRule):
    rules: list[_LegacyNestedSegmentRule]
