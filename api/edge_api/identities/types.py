from typing import TYPE_CHECKING, Any, Literal, NotRequired, TypedDict

if TYPE_CHECKING:
    from edge_api.identities.models import EdgeIdentity


ChangeType = Literal["+", "-", "~"]


class FeatureStateChangeDetails(TypedDict):
    change_type: ChangeType
    identity: "EdgeIdentity"
    old: NotRequired[dict[str, Any]]
    new: NotRequired[dict[str, Any]]


class IdentityChangeset(TypedDict):
    feature_overrides: dict[str, FeatureStateChangeDetails]
