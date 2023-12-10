import typing

from flag_engine.features.models import FeatureStateModel

if typing.TYPE_CHECKING:
    from edge_api.identities.types import ChangeType, FeatureStateChangeDetails


def generate_change_dict(
    change_type: "ChangeType",
    identity_id: int | str | None,
    new: FeatureStateModel | None = None,
    old: FeatureStateModel | None = None,
) -> "FeatureStateChangeDetails":
    if not (new or old):
        raise ValueError("Must provide one of 'new' or 'old'")

    change_dict = {"change_type": change_type}
    if new:
        change_dict["new"] = _get_overridden_feature_state_dict(
            identity_id=identity_id,
            feature_state=new,
        )
    if old:
        change_dict["old"] = _get_overridden_feature_state_dict(
            identity_id=identity_id,
            feature_state=old,
        )

    return change_dict


def _get_overridden_feature_state_dict(
    identity_id: int | str | None,
    feature_state: FeatureStateModel,
) -> dict[str, typing.Any]:
    return {
        **feature_state.dict(),
        "feature_state_value": feature_state.get_value(identity_id),
    }
