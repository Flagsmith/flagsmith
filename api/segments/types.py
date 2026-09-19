from typing import Literal

from flag_engine.segments.types import ConditionOperator, RuleType
from typing_extensions import NotRequired, TypedDict

#: Where a `SegmentContext` came from. Identity overrides have no segment of
#: their own; they are expressed to the engine as a synthetic segment, so that
#: the engine resolves them by priority like any other override.
SegmentSource = Literal["segment", "identity_overrides"]


class SegmentEngineMetadata(TypedDict):
    source: SegmentSource
    #: Absent on synthetic identity-override segments.
    pk: NotRequired[int]


class SegmentCondition(TypedDict):
    property: str | None
    operator: ConditionOperator
    value: str | None
    description: str | None


class _BaseSegmentRule(TypedDict):
    type: RuleType
    conditions: list[SegmentCondition]


class SegmentRule(_BaseSegmentRule):
    # Nested rules are absent rather than empty in some stored trees.
    rules: NotRequired[list["SegmentRule"]]


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


class LegacySegmentRule(_BaseLegacySegmentRule):
    rules: NotRequired[list["LegacySegmentRule"]]
