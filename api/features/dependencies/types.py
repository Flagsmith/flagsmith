import typing


class ReferencingSegment(typing.TypedDict):
    """The segment whose rules hold the `$.flags` condition making up a dependency."""

    id: int
    name: str
    condition_json_path: str


class DependencyEdge(typing.TypedDict):
    """One feature's dependency on another."""

    feature: str
    needs: str
    segment: ReferencingSegment


DependencyPath = list[DependencyEdge]
