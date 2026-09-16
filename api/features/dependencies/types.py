import typing

FeatureName = str
JSONPathStr = str


class ReferencingSegment(typing.TypedDict):
    """The segment whose rules hold the `$.flags` condition making up a dependency."""

    id: int
    name: str
    condition_json_path: str


class ReferencingEnvironment(typing.TypedDict):
    """The environment whose live overrides make up a dependency graph."""

    key: str
    name: str


class DependencyEdge(typing.TypedDict):
    """One feature's dependency on another."""

    feature: str
    needs: str
    segment: ReferencingSegment


DependencyPath = list[DependencyEdge]
