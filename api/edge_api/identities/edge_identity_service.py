import typing
from dataclasses import dataclass

from flag_engine.features.models import FeatureStateModel

from environments.dynamodb.dynamodb_wrapper import DynamoEnvironmentV2Wrapper

ddb_environment_v2_wrapper = DynamoEnvironmentV2Wrapper()


@dataclass
class EdgeIdentityOverride:
    identity_uuid: str
    identifier: str
    feature_state: FeatureStateModel


def get_edge_identity_overrides(
    environment_id: int, feature_id: int = None
) -> typing.List[EdgeIdentityOverride]:
    override_items = ddb_environment_v2_wrapper.get_identity_overrides(
        environment_id, feature_id
    )
    return [
        EdgeIdentityOverride(
            identity_uuid=item["document_key"].split(":")[-1],
            identifier=item["identifier"],
            feature_state=FeatureStateModel.parse_obj(item["feature_state"]),
        )
        for item in override_items
    ]
