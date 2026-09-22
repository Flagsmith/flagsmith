import typing

from segments.types import SegmentRule

FeatureName = str


class _Feature(typing.TypedDict):
    """Either a feature or a prerequisite feature in a dependency graph."""

    id: int
    name: FeatureName


class _ReferencingSegment(typing.TypedDict):
    """The segment whose rules hold the `$.flags` condition making up a dependency."""

    id: int
    name: str
    rules: list[SegmentRule]
    condition_json_path: str
    is_system: bool


class ReferencingEnvironment(typing.TypedDict):
    """The environment whose live overrides make up a dependency graph."""

    key: str
    name: str


class DependencyEdge(typing.TypedDict):
    """One feature's dependency on another."""

    feature: _Feature
    prerequisite: _Feature
    segment: _ReferencingSegment


DependencyPath = list[DependencyEdge]
