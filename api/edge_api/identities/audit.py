import typing

from flag_engine.features.models import FeatureStateModel

if typing.TYPE_CHECKING:
    from edge_api.identities.models import EdgeIdentity


def generate_change_dict(
    change_type: str,
    identity: "EdgeIdentity",
    new: typing.Optional[FeatureStateModel] = None,
    old: typing.Optional[FeatureStateModel] = None,
):
    if not (new or old):
        raise ValueError("Must provide one of 'current' or 'previous'")

    change_dict = {"change_type": change_type}
    if new:
        change_dict["new"] = {
            "enabled": new.enabled,
            "value": new.get_value(identity.id),
        }
    if old:
        change_dict["old"] = {
            "enabled": old.enabled,
            "value": old.get_value(identity.id),
        }

    return change_dict
