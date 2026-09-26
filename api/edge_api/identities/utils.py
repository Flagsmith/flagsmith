import typing

from evaluation.services import get_edge_identity_override_value

if typing.TYPE_CHECKING:
    from flagsmith_schemas.dynamodb import FeatureState

    from edge_api.identities.models import EdgeIdentity
    from edge_api.identities.types import ChangeType, FeatureStateChangeDetails
    from environments.models import Environment


def generate_change_dict(
    change_type: "ChangeType",
    *,
    edge_identity: "EdgeIdentity",
    environment: "Environment",
    new: "FeatureState | None" = None,
    old: "FeatureState | None" = None,
) -> "FeatureStateChangeDetails":
    if not (new or old):
        raise ValueError("Must provide one of 'new' or 'old'")

    change_dict = {"change_type": change_type}
    if new:
        change_dict["new"] = _get_overridden_feature_state_dict(  # type: ignore[assignment]
            edge_identity=edge_identity,
            environment=environment,
            feature_state=new,
        )
    if old:
        change_dict["old"] = _get_overridden_feature_state_dict(  # type: ignore[assignment]
            edge_identity=edge_identity,
            environment=environment,
            feature_state=old,
        )

    return change_dict  # type: ignore[return-value]


def _get_overridden_feature_state_dict(
    *,
    edge_identity: "EdgeIdentity",
    environment: "Environment",
    feature_state: "FeatureState",
) -> dict[str, typing.Any]:
    return {
        **feature_state,
        "feature_state_value": get_edge_identity_override_value(
            edge_identity, feature_state, environment=environment
        ),
    }
