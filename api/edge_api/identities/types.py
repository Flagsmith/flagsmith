from typing import Any, Literal, TypedDict

from typing_extensions import NotRequired

ChangeType = Literal["+", "-", "~"]


class FeatureStateChangeDetails(TypedDict):
    change_type: ChangeType
    old: NotRequired[dict[str, Any]]
    new: NotRequired[dict[str, Any]]


class IdentityChangeset(TypedDict):
    feature_overrides: dict[str, FeatureStateChangeDetails]
