"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from collections.abc import Sequence

from typing_extensions import NotRequired, TypedDict

from features.feature_states.models import FeatureValueType


class FlagValue(TypedDict):
    type: FeatureValueType
    value: str


class Variant(TypedDict):
    id: int
    weight: float  # Percentage between 0 and 100


class SegmentReference(TypedDict):
    id: int


class EnvironmentDefaultRequest(TypedDict, total=False):
    enabled: bool
    value: FlagValue
    variants: Sequence[Variant]


class SegmentOverrideRequest(TypedDict):
    segment: SegmentReference
    enabled: NotRequired[bool]
    priority: NotRequired[int]
    value: NotRequired[FlagValue]
    variants: NotRequired[Sequence[Variant]]


class UpdateFlagRequest(TypedDict, total=False):
    environment_default: EnvironmentDefaultRequest
    segment_overrides: Sequence[SegmentOverrideRequest]


class SegmentOverrideChanges(TypedDict):
    """Changes to write to a segment override.

    Unlike requests, these can clear the override's value, as the legacy
    feature state APIs can.

    TODO: Replace with `SegmentOverrideRequest` after
    https://github.com/Flagsmith/flagsmith/issues/7641
    """

    segment: SegmentReference
    enabled: NotRequired[bool]
    priority: NotRequired[int]
    value: NotRequired[FlagValue | None]
    variants: NotRequired[Sequence[Variant]]


class FlagChanges(TypedDict, total=False):
    """Changes to write to a flag.

    TODO: Replace with `UpdateFlagRequest` after
    https://github.com/Flagsmith/flagsmith/issues/7641
    """

    environment_default: EnvironmentDefaultRequest
    segment_overrides: Sequence[SegmentOverrideChanges]


class EnvironmentDefaultResponse(TypedDict):
    enabled: bool
    value: FlagValue | None
    variants: list[Variant]


class SegmentOverrideResponse(TypedDict):
    segment: SegmentReference
    priority: int
    enabled: bool
    value: FlagValue | None
    variants: list[Variant]


class UpdateFlagResponse(TypedDict):
    environment_default: EnvironmentDefaultResponse
    segment_overrides: list[SegmentOverrideResponse]
