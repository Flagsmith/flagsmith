from typing import TypedDict


class ResolvedIds(TypedDict, total=False):
    """IDs of the entities an API request acts on, as known so far"""

    organisation__id: int
    project__id: int
    feature__id: int
    environment__id: int
    environment__api_key: str
