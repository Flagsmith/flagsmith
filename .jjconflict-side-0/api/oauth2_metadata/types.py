from typing import TypedDict


class ScopeDescription(TypedDict):
    """How a scope is presented to a user asked to consent to it."""

    label: str
    grants: list[str]
